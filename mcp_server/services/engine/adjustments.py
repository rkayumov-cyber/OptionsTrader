"""Adjustment rules engine (Section 5).

Rules A1-A9: time roll, delta breach, vol spike, regime change, etc.
"""

from __future__ import annotations

from mcp_server.engine_models import (
    AdjustmentRule,
    MarketInputs,
    RegimeResult,
    RuleEvaluation,
    RulePriority,
)


# ── Rule Definitions (A1-A9) ─────────────────────────────────────────────

ADJUSTMENT_RULES: dict[str, AdjustmentRule] = {
    "A1": AdjustmentRule(
        rule_id="A1",
        name="Time Roll",
        trigger="dte <= 21",
        action="Roll to next month (same delta) or close",
        rationale="Gamma acceleration beyond 21 DTE [GS Art of Put Selling]",
        priority=RulePriority.HIGH,
    ),
    "A2": AdjustmentRule(
        rule_id="A2",
        name="Time Close",
        trigger="dte <= 7 AND strategy != '0DTE'",
        action="Close position regardless of P&L",
        rationale="Gamma fundamentally changes position character [JPM P&L Attribution]",
        priority=RulePriority.CRITICAL,
    ),
    "A3": AdjustmentRule(
        rule_id="A3",
        name="Delta Breach",
        trigger="short_strike_delta > 30 (from initial 10-20)",
        action="Roll strike further OTM and out in time",
        rationale="Underlying moved significantly toward strike [JPM Resilient Option Carry]",
        priority=RulePriority.HIGH,
    ),
    "A4": AdjustmentRule(
        rule_id="A4",
        name="Strangle Test",
        trigger="tested side breached by > 1 standard deviation",
        action="Close tested side; leave untested as standalone if profitable. Do NOT double down.",
        rationale="[GS Art of Put Selling]",
        priority=RulePriority.HIGH,
    ),
    "A5": AdjustmentRule(
        rule_id="A5",
        name="Delta Hedge",
        trigger="portfolio_delta > +/-15% NAV",
        action="Add delta hedges via futures or ATM options",
        rationale="[Inference from JPM position management framework]",
        priority=RulePriority.HIGH,
    ),
    "A6": AdjustmentRule(
        rule_id="A6",
        name="Vol Spike",
        trigger="vix_1d_change > 5 OR vix_5d_change > 30%",
        action="Reduce all short vega by 50%. If VIX > 35: close ALL naked short vol.",
        rationale="[GS Vol Vitals; GS State of Vol]",
        priority=RulePriority.CRITICAL,
    ),
    "A7": AdjustmentRule(
        rule_id="A7",
        name="Earnings Dodge",
        trigger="days_to_earnings <= 5 AND position is covered_call on that name",
        action="Roll or close calls before earnings",
        rationale="Failure costs 3-6% annually [GS Overwriting 16yr study]",
        priority=RulePriority.HIGH,
    ),
    "A8": AdjustmentRule(
        rule_id="A8",
        name="Regime Change",
        trigger="regime classification changes (e.g., NORMAL -> ELEVATED)",
        action="Review ALL positions. Close any not appropriate for new regime.",
        rationale="[JPM Systematic Vol]",
        priority=RulePriority.CRITICAL,
    ),
    "A9": AdjustmentRule(
        rule_id="A9",
        name="Correlation Spike",
        trigger="implied_corr rises above 80th pctile within 5 days",
        action="Close all dispersion trades. Review short vol positions for systemic risk.",
        rationale="[JPM Equity Vol Strategy]",
        priority=RulePriority.HIGH,
    ),
}


class AdjustmentEngine:
    """Evaluates adjustment rules A1-A9 against position and market state."""

    def __init__(self):
        self.rules = ADJUSTMENT_RULES

    def evaluate(
        self,
        position: dict,
        regime: RegimeResult,
        inputs: MarketInputs,
        previous_regime: RegimeResult | None = None,
    ) -> list[RuleEvaluation]:
        """Evaluate all adjustment rules for a given position.

        Args:
            position: Position dict with keys like 'dte', 'strategy', 'delta',
                      'portfolio_delta_pct', 'is_0dte', 'is_covered_call',
                      'underlying_symbol', 'is_naked_short', 'is_dispersion'.
            regime: Current regime classification.
            inputs: Current market inputs.
            previous_regime: Previous regime for change detection (A8).

        Returns:
            List of rule evaluations, only including triggered rules.
        """
        results: list[RuleEvaluation] = []

        # A1: Time Roll
        dte = position.get("dte", 999)
        if dte <= 21 and dte > 7:
            results.append(RuleEvaluation(
                rule_id="A1", rule_name="Time Roll", triggered=True,
                priority=RulePriority.HIGH,
                action=self.rules["A1"].action,
                details=f"Position DTE={dte}, below 21-day roll threshold",
            ))

        # A2: Time Close
        if dte <= 7 and not position.get("is_0dte", False):
            results.append(RuleEvaluation(
                rule_id="A2", rule_name="Time Close", triggered=True,
                priority=RulePriority.CRITICAL,
                action=self.rules["A2"].action,
                details=f"Position DTE={dte}, gamma acceleration zone",
            ))

        # A3: Delta Breach
        current_delta = position.get("current_delta", 0)
        initial_delta = position.get("initial_delta", 15)
        if abs(current_delta) > 30 and abs(initial_delta) <= 20:
            results.append(RuleEvaluation(
                rule_id="A3", rule_name="Delta Breach", triggered=True,
                priority=RulePriority.HIGH,
                action=self.rules["A3"].action,
                details=f"Delta moved from {initial_delta} to {current_delta}",
            ))

        # A4: Strangle Test
        if position.get("strategy") in ("short_strangle", "iron_condor"):
            tested_breach = position.get("tested_breach_std", 0)
            if tested_breach > 1.0:
                results.append(RuleEvaluation(
                    rule_id="A4", rule_name="Strangle Test", triggered=True,
                    priority=RulePriority.HIGH,
                    action=self.rules["A4"].action,
                    details=f"Tested side breached by {tested_breach:.1f} std deviations",
                ))

        # A5: Delta Hedge
        portfolio_delta_pct = position.get("portfolio_delta_pct", 0)
        if abs(portfolio_delta_pct) > 0.15:
            results.append(RuleEvaluation(
                rule_id="A5", rule_name="Delta Hedge", triggered=True,
                priority=RulePriority.HIGH,
                action=self.rules["A5"].action,
                details=f"Portfolio delta at {portfolio_delta_pct:.1%} of NAV",
            ))

        # A6: Vol Spike
        vix_1d = inputs.vol.vix_1d_change
        vix_5d_pct = (
            inputs.vol.vix_5d_change / max(inputs.vol.vix - inputs.vol.vix_5d_change, 1)
        ) if inputs.vol.vix > 0 else 0
        if vix_1d > 5 or vix_5d_pct > 0.30:
            action = self.rules["A6"].action
            if inputs.vol.vix > 35:
                action = "CRITICAL: VIX > 35 - close ALL naked short vol immediately"
            results.append(RuleEvaluation(
                rule_id="A6", rule_name="Vol Spike", triggered=True,
                priority=RulePriority.CRITICAL,
                action=action,
                details=f"VIX 1d change: {vix_1d:+.1f}, 5d change: {vix_5d_pct:.1%}",
            ))

        # A7: Earnings Dodge
        if (position.get("is_covered_call", False) and
                inputs.events.days_to_earnings <= 5):
            results.append(RuleEvaluation(
                rule_id="A7", rule_name="Earnings Dodge", triggered=True,
                priority=RulePriority.HIGH,
                action=self.rules["A7"].action,
                details=f"Earnings in {inputs.events.days_to_earnings} days for covered call",
            ))

        # A8: Regime Change
        if previous_regime and previous_regime.regime != regime.regime:
            results.append(RuleEvaluation(
                rule_id="A8", rule_name="Regime Change", triggered=True,
                priority=RulePriority.CRITICAL,
                action=self.rules["A8"].action,
                details=f"Regime changed: {previous_regime.regime.value} -> {regime.regime.value}",
            ))

        # A9: Correlation Spike
        if (inputs.correlation.corr_pctile_1y > 80 and
                position.get("is_dispersion", False)):
            results.append(RuleEvaluation(
                rule_id="A9", rule_name="Correlation Spike", triggered=True,
                priority=RulePriority.HIGH,
                action=self.rules["A9"].action,
                details=f"Implied correlation at {inputs.correlation.corr_pctile_1y:.0f}th percentile",
            ))

        return results

    def get_all_rules(self) -> list[AdjustmentRule]:
        """Return all adjustment rule definitions."""
        return list(self.rules.values())
