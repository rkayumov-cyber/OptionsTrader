"""Decision engine facade.

Orchestrates all engine components into a unified API.
"""

from __future__ import annotations

from datetime import datetime

from mcp_server.engine_models import (
    ConflictScenario,
    DayOfWeek,
    EventPlaybook,
    EventType,
    FullAnalysisResult,
    MarketInputs,
    PositionHealthCheck,
    RegimeResult,
    RuleEvaluation,
    StrategyFamily,
    StrategyObjective,
    StrategyRecommendation,
    StrategyTemplate,
    TailRiskAssessment,
    ZeroDTEDayInfo,
    ZeroDTEPlaybook,
)
from .adjustments import AdjustmentEngine
from .conflicts import ConflictResolver
from .exits import ExitEngine
from .market_inputs import MarketInputsCollector
from .playbooks import EventPlaybooks
from .regime import RegimeClassifier
from .reference_tables import ReferenceTables
from .selector import StrategySelector
from .sizing import PositionSizer
from .strategies import StrategyUniverse
from .tail_risk import TailRiskManager


class DecisionEngine:
    """Unified facade for the options trading decision engine.

    Orchestrates regime classification, strategy selection, position sizing,
    adjustment/exit rules, event playbooks, tail risk, and conflict resolution.
    """

    def __init__(self, provider=None):
        self.inputs_collector = MarketInputsCollector(provider=provider)
        self.regime_classifier = RegimeClassifier()
        self.sizer = PositionSizer()
        self.selector = StrategySelector()
        self.adjustment_engine = AdjustmentEngine()
        self.exit_engine = ExitEngine()
        self.tail_risk_manager = TailRiskManager()
        self.conflict_resolver = ConflictResolver()

        # Regime history for change detection
        self._previous_regime: RegimeResult | None = None
        self._last_inputs: MarketInputs | None = None

    async def full_analysis(
        self,
        nav: float = 100_000,
        objective: str = "income",
        positions: list[dict] | None = None,
    ) -> FullAnalysisResult:
        """Run the complete decision engine pipeline.

        Args:
            nav: Portfolio net asset value.
            objective: "income" | "directional" | "hedging" | "event" | "relative_value" | "all"
            positions: Optional list of position dicts for health checks.

        Returns:
            Complete analysis including regime, recommendations, tail risk,
            conflicts, active playbook, and position health checks.
        """
        inputs = await self.inputs_collector.collect()
        self._last_inputs = inputs

        # 1. Classify regime
        regime = self.regime_classifier.classify(inputs)

        # 2. Get strategy recommendations
        recommendation = self.selector.select(regime, inputs, objective, nav)

        # 3. Assess tail risk
        tail_risk = self.tail_risk_manager.assess(inputs)

        # 4. Check conflicts
        conflicts = self.conflict_resolver.check_conflicts(regime, inputs)

        # 5. Get active playbook if event window
        active_playbook = None
        if regime.event_active and regime.event_type != EventType.NONE:
            try:
                active_playbook = EventPlaybooks.get_playbook(regime.event_type)
            except ValueError:
                pass

        # 6. Evaluate position health
        health_checks = []
        if positions:
            for pos in positions:
                health = self._evaluate_position(pos, regime, inputs)
                health_checks.append(health)

        # Update regime history
        self._previous_regime = regime

        return FullAnalysisResult(
            regime=regime,
            recommendation=recommendation,
            tail_risk=tail_risk,
            conflicts=conflicts,
            active_playbook=active_playbook,
            position_health=health_checks,
            market_inputs=inputs,
        )

    async def get_regime(self) -> RegimeResult:
        """Classify and return the current market regime."""
        inputs = await self.inputs_collector.collect()
        self._last_inputs = inputs
        regime = self.regime_classifier.classify(inputs)
        self._previous_regime = regime
        return regime

    async def get_recommendations(
        self, nav: float = 100_000, objective: str = "income"
    ) -> StrategyRecommendation:
        """Get strategy recommendations for current market conditions."""
        inputs = await self.inputs_collector.collect()
        self._last_inputs = inputs
        regime = self.regime_classifier.classify(inputs)
        self._previous_regime = regime
        return self.selector.select(regime, inputs, objective, nav)

    async def evaluate_position(self, position: dict) -> PositionHealthCheck:
        """Evaluate a single position against adjustment and exit rules."""
        inputs = await self.inputs_collector.collect()
        self._last_inputs = inputs
        regime = self.regime_classifier.classify(inputs)
        return self._evaluate_position(position, regime, inputs)

    async def get_tail_risk(self) -> TailRiskAssessment:
        """Get current tail risk assessment."""
        inputs = await self.inputs_collector.collect()
        self._last_inputs = inputs
        return self.tail_risk_manager.assess(inputs)

    async def get_conflicts(self) -> list[ConflictScenario]:
        """Get currently detected signal conflicts."""
        inputs = await self.inputs_collector.collect()
        self._last_inputs = inputs
        regime = self.regime_classifier.classify(inputs)
        return self.conflict_resolver.check_conflicts(regime, inputs)

    async def get_all_conflicts(self) -> list[ConflictScenario]:
        """Get all conflict scenarios with detection status."""
        inputs = await self.inputs_collector.collect()
        self._last_inputs = inputs
        regime = self.regime_classifier.classify(inputs)
        return self.conflict_resolver.check_all(regime, inputs)

    def get_playbook(self, event_type: str) -> EventPlaybook:
        """Get a specific event playbook."""
        et = EventType(event_type)
        return EventPlaybooks.get_playbook(et)

    def get_zero_dte_playbook(self) -> ZeroDTEPlaybook:
        """Get the 0DTE playbook."""
        return EventPlaybooks.get_zero_dte()

    def get_zero_dte_day(self, day: str) -> ZeroDTEDayInfo:
        """Get 0DTE recommendation for a specific day."""
        d = DayOfWeek(day)
        return EventPlaybooks.get_zero_dte_day(d)

    def get_strategy_universe(self) -> list[StrategyTemplate]:
        """Get all strategy templates."""
        return StrategyUniverse.list_all()

    def get_strategies_by_family(self, family: str) -> list[StrategyTemplate]:
        """Get strategies filtered by family."""
        f = StrategyFamily(family)
        return StrategyUniverse.by_family(f)

    def get_reference_table(self, name: str) -> list:
        """Get a reference data table by name."""
        return ReferenceTables.get_table(name)

    def list_reference_tables(self) -> list[str]:
        """List available reference tables."""
        return ReferenceTables.list_tables()

    def _evaluate_position(
        self,
        position: dict,
        regime: RegimeResult,
        inputs: MarketInputs,
    ) -> PositionHealthCheck:
        """Internal position evaluation against A1-A9 and X1-X7."""
        adj_rules = self.adjustment_engine.evaluate(
            position, regime, inputs, self._previous_regime
        )
        exit_rules = self.exit_engine.evaluate(
            position, regime, inputs, self._previous_regime
        )

        triggered = adj_rules + exit_rules
        critical_count = sum(
            1 for r in triggered
            if r.priority.value == "CRITICAL"
        )

        # Determine recommended action
        if critical_count > 0:
            action = "IMMEDIATE ACTION REQUIRED: " + "; ".join(
                r.action for r in triggered if r.priority.value == "CRITICAL"
            )
        elif len(triggered) > 0:
            action = "Review: " + "; ".join(r.action for r in triggered[:3])
        else:
            action = "No action needed - position healthy"

        return PositionHealthCheck(
            position_id=position.get("id", "unknown"),
            adjustment_rules=adj_rules,
            exit_rules=exit_rules,
            triggered_count=len(triggered),
            critical_count=critical_count,
            recommended_action=action,
        )
