"""Exit rules engine (Section 6).

Rules X1-X7: profit targets, stop losses, time stops, regime exits, daily P&L.
"""

from __future__ import annotations

from mcp_server.engine_models import (
    ExitRule,
    MarketInputs,
    RegimeResult,
    RuleEvaluation,
    RulePriority,
    StrategyFamily,
)


# ── Rule Definitions (X1-X7) ─────────────────────────────────────────────

EXIT_RULES: dict[str, ExitRule] = {
    "X1": ExitRule(
        rule_id="X1",
        name="Credit Profit Target",
        trigger="unrealized_profit >= 50% of max_profit",
        action="Close. Set limit order at entry.",
        rationale="Maximizes risk-adjusted returns [GS Art of Put Selling 10yr]",
        applies_to="ALL short_premium strategies",
    ),
    "X2": ExitRule(
        rule_id="X2",
        name="Debit Profit Target",
        trigger="unrealized_profit >= 100% of debit_paid",
        action="Close (2:1 R/R achieved). For event trades: close within 24hrs post-event.",
        rationale="[GS Trading Events]",
        applies_to="ALL long_premium strategies",
    ),
    "X3": ExitRule(
        rule_id="X3",
        name="Credit Stop Loss",
        trigger="unrealized_loss >= 2x premium_received",
        action="Close. Expected recovery is negative beyond this point.",
        rationale="[GS Art of Put Selling]",
        applies_to="ALL short_premium strategies",
    ),
    "X4": ExitRule(
        rule_id="X4",
        name="Debit Stop Loss",
        trigger="unrealized_loss >= 50% of premium_paid AND no catalyst change",
        action="Close. Re-evaluate thesis before re-entering.",
        applies_to="ALL long_premium strategies",
    ),
    "X5": ExitRule(
        rule_id="X5",
        name="Time Stop",
        trigger="dte <= 7 AND strategy_type != '0DTE'",
        action="Close. Gamma acceleration makes position fundamentally different.",
        rationale="[JPM P&L Attribution; JPM Same-day Options]",
    ),
    "X6": ExitRule(
        rule_id="X6",
        name="Regime Exit",
        trigger="regime_classifier output changes to incompatible regime",
        action="Close ALL positions not appropriate for new regime immediately.",
        rationale="[JPM Systematic Vol]",
    ),
    "X7": ExitRule(
        rule_id="X7",
        name="Daily P&L Stop",
        trigger="daily_pnl_loss > 1.5% of NAV",
        action="Reduce exposure by 50%. No new trades today.",
        rationale="[JPM Systematic Vol]",
    ),
}


class ExitEngine:
    """Evaluates exit rules X1-X7 against position and market state."""

    def __init__(self):
        self.rules = EXIT_RULES

    def evaluate(
        self,
        position: dict,
        regime: RegimeResult,
        inputs: MarketInputs,
        previous_regime: RegimeResult | None = None,
        nav: float = 100_000,
    ) -> list[RuleEvaluation]:
        """Evaluate all exit rules for a given position.

        Args:
            position: Position dict with keys:
                - family: "short_premium" | "long_premium"
                - unrealized_pnl: float (dollar P&L)
                - max_profit: float (max possible profit)
                - premium_paid: float (for debit trades)
                - premium_received: float (for credit trades)
                - dte: int
                - is_0dte: bool
                - regime_allowed: list[str] (allowed regimes for this strategy)
                - daily_pnl: float (total portfolio daily P&L)
            regime: Current regime classification.
            inputs: Current market inputs.
            previous_regime: Previous regime for change detection (X6).
            nav: Portfolio NAV for P&L stop calculations.

        Returns:
            List of triggered rule evaluations.
        """
        results: list[RuleEvaluation] = []
        family = position.get("family", "")
        pnl = position.get("unrealized_pnl", 0)

        # X1: Credit Profit Target
        if family == "short_premium":
            max_profit = position.get("max_profit", 0)
            if max_profit > 0 and pnl >= max_profit * 0.50:
                results.append(RuleEvaluation(
                    rule_id="X1", rule_name="Credit Profit Target", triggered=True,
                    priority=RulePriority.HIGH,
                    action=self.rules["X1"].action,
                    details=f"Profit {pnl:.2f} >= 50% of max {max_profit:.2f}",
                ))

        # X2: Debit Profit Target
        if family == "long_premium":
            premium_paid = position.get("premium_paid", 0)
            if premium_paid > 0 and pnl >= premium_paid:
                results.append(RuleEvaluation(
                    rule_id="X2", rule_name="Debit Profit Target", triggered=True,
                    priority=RulePriority.HIGH,
                    action=self.rules["X2"].action,
                    details=f"Profit {pnl:.2f} >= 100% of debit {premium_paid:.2f}",
                ))

        # X3: Credit Stop Loss
        if family == "short_premium":
            premium_received = position.get("premium_received", 0)
            if premium_received > 0 and pnl < 0 and abs(pnl) >= premium_received * 2:
                results.append(RuleEvaluation(
                    rule_id="X3", rule_name="Credit Stop Loss", triggered=True,
                    priority=RulePriority.CRITICAL,
                    action=self.rules["X3"].action,
                    details=f"Loss {pnl:.2f} >= 2x premium {premium_received:.2f}",
                ))

        # X4: Debit Stop Loss
        if family == "long_premium":
            premium_paid = position.get("premium_paid", 0)
            if premium_paid > 0 and pnl < 0 and abs(pnl) >= premium_paid * 0.50:
                results.append(RuleEvaluation(
                    rule_id="X4", rule_name="Debit Stop Loss", triggered=True,
                    priority=RulePriority.HIGH,
                    action=self.rules["X4"].action,
                    details=f"Loss {pnl:.2f} >= 50% of debit {premium_paid:.2f}",
                ))

        # X5: Time Stop
        dte = position.get("dte", 999)
        if dte <= 7 and not position.get("is_0dte", False):
            results.append(RuleEvaluation(
                rule_id="X5", rule_name="Time Stop", triggered=True,
                priority=RulePriority.CRITICAL,
                action=self.rules["X5"].action,
                details=f"DTE={dte}, gamma acceleration zone",
            ))

        # X6: Regime Exit
        if previous_regime and previous_regime.regime != regime.regime:
            allowed = position.get("regime_allowed", [])
            if allowed and regime.regime.value not in allowed and "ALL" not in allowed:
                results.append(RuleEvaluation(
                    rule_id="X6", rule_name="Regime Exit", triggered=True,
                    priority=RulePriority.CRITICAL,
                    action=self.rules["X6"].action,
                    details=f"New regime {regime.regime.value} not in allowed {allowed}",
                ))

        # X7: Daily P&L Stop
        daily_pnl = position.get("daily_pnl", 0)
        if nav > 0 and daily_pnl < 0 and abs(daily_pnl / nav) > 0.015:
            results.append(RuleEvaluation(
                rule_id="X7", rule_name="Daily P&L Stop", triggered=True,
                priority=RulePriority.CRITICAL,
                action=self.rules["X7"].action,
                details=f"Daily loss {daily_pnl/nav:.2%} exceeds 1.5% limit",
            ))

        return results

    def get_all_rules(self) -> list[ExitRule]:
        """Return all exit rule definitions."""
        return list(self.rules.values())
