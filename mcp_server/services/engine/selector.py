"""Strategy selector engine (Section 4).

7 entry gates, 6-dimension scoring, parameterization, top-3 pipeline.
"""

from __future__ import annotations

from mcp_server.engine_models import (
    Confidence,
    GateCheckResult,
    MarketInputs,
    RecommendationType,
    RegimeResult,
    StrategyCandidate,
    StrategyFamily,
    StrategyObjective,
    StrategyParams,
    StrategyRecommendation,
    StrategyScore,
    StrategyTemplate,
    VolRegime,
)
from .sizing import SIZE_MULTIPLIER, vvix_adjustment
from .strategies import StrategyUniverse


# Delta adjustment factors by regime
_DELTA_ADJUSTMENTS: dict[str, float] = {
    "VERY_LOW": 1.2,
    "LOW": 1.1,
    "NORMAL": 1.0,
    "ELEVATED": 0.8,
    "HIGH": 0.6,
    "CRISIS": 0.5,
    "EXTREME": 0.5,
    "LIQUIDITY_STRESS": 0.7,
}


def _adjust_delta(base_delta: int, regime_name: str) -> int:
    """Regime-adjusted delta selection."""
    factor = _DELTA_ADJUSTMENTS.get(regime_name, 1.0)
    return max(1, round(base_delta * factor))


class StrategySelector:
    """Selects, scores, and parameterizes strategy recommendations."""

    def __init__(self, universe: StrategyUniverse | None = None):
        self.universe = universe or StrategyUniverse()

    def select(
        self,
        regime: RegimeResult,
        inputs: MarketInputs,
        objective: str = "income",
        nav: float = 100_000,
    ) -> StrategyRecommendation:
        """Run the full selection pipeline: gates -> score -> parameterize -> rank."""
        candidates: list[StrategyCandidate] = []

        for name, template in self.universe.TEMPLATES.items():
            # Step 1: Entry gates
            gates = self._check_gates(template, regime, inputs)
            all_passed = all(g.passed for g in gates)
            if not all_passed:
                continue

            # Step 2: Objective filter
            if not self._matches_objective(template, objective):
                continue

            # Step 3: Score
            scores = self._score(template, regime, inputs)

            # Step 4: Parameterize
            params = self._parameterize(template, regime, inputs)

            candidates.append(
                StrategyCandidate(
                    name=name,
                    template=template,
                    scores=scores,
                    params=params,
                    gates=gates,
                )
            )

        # Sort by total score descending
        candidates.sort(key=lambda c: c.scores.total, reverse=True)
        top = candidates[:3]

        # Fallback logic
        if len(top) == 0:
            return StrategyRecommendation(
                recommendation=RecommendationType.NO_TRADE,
                regime=regime,
                note="No strategy passes all filters in current regime",
            )

        if top[0].scores.total < 5.0:
            return StrategyRecommendation(
                recommendation=RecommendationType.LOW_CONVICTION,
                strategies=top,
                regime=regime,
                note="Reduce size by 50% or wait for better setup",
            )

        if regime.confidence == Confidence.LOW:
            top = [c for c in top if c.template.legs >= 2]
            if not top:
                return StrategyRecommendation(
                    recommendation=RecommendationType.REGIME_UNCERTAIN,
                    regime=regime,
                    note="Mixed signals; no defined-risk strategies available. WAIT.",
                )
            return StrategyRecommendation(
                recommendation=RecommendationType.TRADE_CAUTIOUS,
                strategies=top,
                regime=regime,
                note="Low confidence regime - defined risk only, 50% size",
            )

        return StrategyRecommendation(
            recommendation=RecommendationType.TRADE,
            strategies=top,
            regime=regime,
        )

    # ── Entry Gates (Section 4.1) ─────────────────────────────────────

    def _check_gates(
        self,
        strategy: StrategyTemplate,
        regime: RegimeResult,
        inputs: MarketInputs,
    ) -> list[GateCheckResult]:
        gates = []

        # GATE 1: IV Rank Filter
        if strategy.family == StrategyFamily.SHORT_PREMIUM:
            passed = inputs.vol.vix_percentile_1y >= 25
            gates.append(GateCheckResult(
                gate_name="G1_iv_rank",
                passed=passed,
                reason="" if passed else "IV rank below 25th pctile - insufficient premium",
            ))

        # GATE 2: Event Avoidance
        if strategy.event_block and regime.event_active:
            ev = inputs.events
            blocked = False
            if regime.event_type.value in ("FOMC", "CPI", "NFP"):
                if min(ev.days_to_fomc, ev.days_to_cpi, ev.days_to_nfp) <= 10:
                    blocked = True
            if regime.event_type.value == "EARNINGS" and ev.days_to_earnings <= 5:
                blocked = True
            gates.append(GateCheckResult(
                gate_name="G2_event_avoidance",
                passed=not blocked,
                reason="" if not blocked else f"Event ({regime.event_type.value}) within blocking window",
            ))

        # GATE 3: Liquidity
        passed = inputs.liquidity.spx_bid_ask <= 0.30
        gates.append(GateCheckResult(
            gate_name="G3_liquidity",
            passed=passed,
            reason="" if passed else "Bid-ask > 30% of mid - abort entry",
        ))

        # GATE 4: Theta/Gamma Ratio (placeholder - needs live Greeks)
        if strategy.family == StrategyFamily.SHORT_PREMIUM:
            gates.append(GateCheckResult(
                gate_name="G4_theta_gamma",
                passed=True,
                reason="Theta/gamma check deferred to execution",
            ))

        # GATE 5: Regime Compatibility
        regime_name = regime.regime.value
        allowed = strategy.regime_allowed
        excluded = strategy.regime_excluded
        if "ALL" in allowed:
            passed = regime_name not in excluded
        else:
            passed = regime_name in allowed and regime_name not in excluded
        gates.append(GateCheckResult(
            gate_name="G5_regime_compat",
            passed=passed,
            reason="" if passed else f"Strategy not allowed in {regime_name} regime",
        ))

        # GATE 6: VVIX Stability
        if regime.vol_unstable and strategy.family == StrategyFamily.SHORT_PREMIUM:
            passed = strategy.legs >= 2
            gates.append(GateCheckResult(
                gate_name="G6_vvix_stability",
                passed=passed,
                reason="" if passed else "VVIX > 22 - no naked short vol",
            ))

        # GATE 7: Strategy-specific IV rank constraints
        if strategy.iv_rank_min is not None:
            passed = inputs.vol.vix_percentile_1y >= strategy.iv_rank_min
            gates.append(GateCheckResult(
                gate_name="G7_iv_rank_min",
                passed=passed,
                reason="" if passed else f"IV rank {inputs.vol.vix_percentile_1y:.0f} below strategy min {strategy.iv_rank_min}",
            ))
        if strategy.iv_rank_max is not None:
            passed = inputs.vol.vix_percentile_1y <= strategy.iv_rank_max
            gates.append(GateCheckResult(
                gate_name="G7_iv_rank_max",
                passed=passed,
                reason="" if passed else f"IV rank {inputs.vol.vix_percentile_1y:.0f} above strategy max {strategy.iv_rank_max}",
            ))
        if strategy.vix_max is not None:
            passed = inputs.vol.vix <= strategy.vix_max
            gates.append(GateCheckResult(
                gate_name="G7_vix_max",
                passed=passed,
                reason="" if passed else f"VIX {inputs.vol.vix:.1f} above strategy max {strategy.vix_max}",
            ))

        return gates

    # ── Objective Filter ──────────────────────────────────────────────

    @staticmethod
    def _matches_objective(strategy: StrategyTemplate, objective: str) -> bool:
        obj_map = {
            "income": lambda s: s.family == StrategyFamily.SHORT_PREMIUM,
            "directional": lambda s: s.objective in (
                StrategyObjective.DIRECTIONAL_BULLISH,
                StrategyObjective.DIRECTIONAL_BEARISH,
                StrategyObjective.SPOT_RECOVERY,
            ),
            "hedging": lambda s: s.family == StrategyFamily.HEDGING,
            "event": lambda s: s.event_required,
            "relative_value": lambda s: s.family == StrategyFamily.RELATIVE_VALUE,
            "tail": lambda s: s.family == StrategyFamily.TAIL_TRADING,
            "all": lambda _: True,
        }
        matcher = obj_map.get(objective, obj_map["all"])
        return matcher(strategy)

    # ── Scoring Model (Section 4.2) ───────────────────────────────────

    @staticmethod
    def _score(
        strategy: StrategyTemplate,
        regime: RegimeResult,
        inputs: MarketInputs,
    ) -> StrategyScore:
        # DIMENSION 1: EDGE (25% weight)
        iv_rank_score = inputs.vol.vix_percentile_1y / 10.0
        if strategy.family == StrategyFamily.SHORT_PREMIUM:
            iv_rv_bonus = min(inputs.vol.iv_rv_spread / 1.0, 3.0)
            edge = min(iv_rank_score + iv_rv_bonus, 10.0)
        else:
            edge = max(10.0 - iv_rank_score, 0.0)

        # DIMENSION 2: CARRY vs CONVEXITY FIT (20% weight)
        if strategy.objective in (
            StrategyObjective.INCOME,
            StrategyObjective.CARRY_WITH_PROTECTION,
        ):
            carry_fit = 8.0
            if regime.regime in (VolRegime.ELEVATED, VolRegime.HIGH):
                carry_fit = 6.0
        elif strategy.objective in (
            StrategyObjective.TAIL_HEDGE,
            StrategyObjective.SYSTEMATIC_TAIL,
            StrategyObjective.EVENT_VOL,
        ):
            carry_fit = 8.0 if inputs.vol.vix_percentile_1y < 30 else 5.0
        else:
            carry_fit = 5.0

        # DIMENSION 3: TAIL RISK EXPOSURE (20% weight, 10=least risk)
        legs = strategy.legs
        if legs >= 4:
            tail = 9.0
        elif legs >= 2:
            tail = 7.0
        elif legs == 1:
            if strategy.family == StrategyFamily.SHORT_PREMIUM:
                tail = 3.0
                if regime.regime == VolRegime.ELEVATED:
                    tail = 2.0
            else:
                tail = 8.0
        else:
            tail = 5.0

        # DIMENSION 4: ROBUSTNESS / WIN RATE (15% weight)
        win_rate = strategy.win_rate or 0.55
        sharpe = strategy.sharpe_hist or 0.50
        robust = min((win_rate * 10) * 0.6 + (sharpe * 5) * 0.4, 10.0)

        # DIMENSION 5: LIQUIDITY (10% weight)
        ba_pct = inputs.liquidity.spx_bid_ask * 100
        if ba_pct < 5:
            liquid = 10.0
        elif ba_pct < 10:
            liquid = 8.0
        elif ba_pct < 20:
            liquid = 5.0
        elif ba_pct < 30:
            liquid = 3.0
        else:
            liquid = 0.0

        # DIMENSION 6: COMPLEXITY PENALTY (10% weight, 10=simplest)
        if legs == 1:
            complexity = 10.0
        elif legs == 2:
            complexity = 8.0
        elif legs == 3:
            complexity = 5.0
        else:
            complexity = 3.0

        total = (
            0.25 * edge
            + 0.20 * carry_fit
            + 0.20 * tail
            + 0.15 * robust
            + 0.10 * liquid
            + 0.10 * complexity
        )

        return StrategyScore(
            total=round(total, 2),
            edge=round(edge, 2),
            carry_fit=round(carry_fit, 2),
            tail_risk=round(tail, 2),
            robustness=round(robust, 2),
            liquidity=round(liquid, 2),
            complexity=round(complexity, 2),
        )

    # ── Parameterization (Section 4.3) ────────────────────────────────

    @staticmethod
    def _parameterize(
        strategy: StrategyTemplate,
        regime: RegimeResult,
        inputs: MarketInputs,
    ) -> StrategyParams:
        regime_name = regime.regime.value

        # Delta adjustment
        delta = None
        deltas = None
        if isinstance(strategy.base_delta, dict):
            deltas = {
                leg: _adjust_delta(d, regime_name)
                for leg, d in strategy.base_delta.items()
            }
        elif isinstance(strategy.base_delta, int):
            delta = _adjust_delta(strategy.base_delta, regime_name)

        # DTE adjustment
        base_dte = strategy.base_dte
        if isinstance(base_dte, str):
            dte = 37  # default for string-based DTEs (event-linked)
        else:
            dte = base_dte
            if regime.event_active and not strategy.event_required:
                ev = inputs.events
                event_days = min(
                    ev.days_to_fomc, ev.days_to_cpi,
                    ev.days_to_nfp, ev.days_to_earnings,
                )
                dte = max(event_days + 10, dte)

        # Size multiplier
        sell_mult, buy_mult = SIZE_MULTIPLIER.get(
            regime.regime, (0.50, 0.75)
        )
        mult = sell_mult if strategy.family == StrategyFamily.SHORT_PREMIUM else buy_mult
        mult *= vvix_adjustment(inputs.vol.vvix)
        if regime.confidence == Confidence.LOW:
            mult *= 0.50

        return StrategyParams(
            delta=delta,
            deltas=deltas,
            dte=dte,
            size_multiplier=round(mult, 2),
            profit_target=strategy.profit_target,
            stop_loss=strategy.stop_loss,
            roll_dte=strategy.roll_dte,
        )
