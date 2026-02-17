"""Position sizing model (Section 2).

Regime multipliers, VVIX adjustment, fixed premium sizing, risk limit checks.
"""

from mcp_server.engine_models import (
    Confidence,
    MarketInputs,
    PositionSizeResult,
    RegimeResult,
    RiskLimits,
    SizeMultipliers,
    VolRegime,
)

# Regime -> (sell_premium_mult, buy_premium_mult)
SIZE_MULTIPLIER: dict[VolRegime, tuple[float, float]] = {
    VolRegime.VERY_LOW: (1.00, 0.50),
    VolRegime.LOW: (1.00, 0.75),
    VolRegime.NORMAL: (0.75, 1.00),
    VolRegime.ELEVATED: (0.50, 1.00),
    VolRegime.HIGH: (0.25, 1.00),
    VolRegime.EXTREME: (0.00, 1.00),
    VolRegime.CRISIS: (0.00, 1.00),
    VolRegime.LIQUIDITY_STRESS: (0.25, 0.75),
}

DEFAULT_RISK_LIMITS = RiskLimits()


def vvix_adjustment(vvix: float) -> float:
    """VVIX-based size adjustment [GS Vol Vitals: VVIX > 22 = reduce 25-50%]."""
    if vvix <= 18:
        return 1.00
    if vvix <= 22:
        return 0.85
    if vvix <= 28:
        return 0.65
    return 0.50


def fixed_premium_size(nav: float, budget_pct: float = 0.005) -> float:
    """Fixed premium sizing: allocate 0.5% of NAV per trade in premium.

    [JPM Equity Vol Strategy] - Allocate fixed dollar premium per trade,
    NOT fixed notional. This naturally reduces size when vol is high.
    """
    return nav * budget_pct


class PositionSizer:
    """Calculates position sizes based on regime, VVIX, and risk limits."""

    def __init__(self, risk_limits: RiskLimits | None = None):
        self.limits = risk_limits or DEFAULT_RISK_LIMITS

    def calculate(
        self,
        nav: float,
        regime: RegimeResult,
        inputs: MarketInputs,
        is_sell_premium: bool = True,
        budget_pct: float = 0.005,
        portfolio_vega: float = 0.0,
        portfolio_delta: float = 0.0,
        daily_pnl: float = 0.0,
        weekly_pnl: float = 0.0,
    ) -> PositionSizeResult:
        """Calculate position size with all adjustments and limit checks."""
        sell_mult, buy_mult = SIZE_MULTIPLIER.get(
            regime.regime, (0.50, 0.75)
        )
        vvix_adj = vvix_adjustment(inputs.vol.vvix)
        conf_adj = 0.50 if regime.confidence == Confidence.LOW else 1.0

        final_sell = round(sell_mult * vvix_adj * conf_adj, 4)
        final_buy = round(buy_mult * vvix_adj * conf_adj, 4)

        multiplier = final_sell if is_sell_premium else final_buy
        premium_budget = fixed_premium_size(nav, budget_pct) * multiplier

        multipliers = SizeMultipliers(
            sell_premium=sell_mult,
            buy_premium=buy_mult,
            vvix_adjustment=vvix_adj,
            confidence_adjustment=conf_adj,
            final_sell=final_sell,
            final_buy=final_buy,
        )

        # Risk limit checks
        breaches = self._check_limits(
            nav, portfolio_vega, portfolio_delta, daily_pnl, weekly_pnl
        )

        return PositionSizeResult(
            premium_budget=round(premium_budget, 2),
            size_multiplier=multiplier,
            multiplier_breakdown=multipliers,
            risk_limit_breaches=breaches,
            within_limits=len(breaches) == 0,
        )

    def _check_limits(
        self,
        nav: float,
        portfolio_vega: float,
        portfolio_delta: float,
        daily_pnl: float,
        weekly_pnl: float,
    ) -> list[str]:
        breaches = []
        if nav > 0:
            if abs(portfolio_vega / nav) > self.limits.max_portfolio_vega:
                breaches.append(
                    f"Portfolio vega {portfolio_vega/nav:.4f} exceeds "
                    f"limit {self.limits.max_portfolio_vega}"
                )
            if abs(portfolio_delta / nav) > self.limits.max_portfolio_delta:
                breaches.append(
                    f"Portfolio delta {portfolio_delta/nav:.2%} exceeds "
                    f"limit {self.limits.max_portfolio_delta:.0%}"
                )
            if daily_pnl < 0 and abs(daily_pnl / nav) > self.limits.daily_pnl_stop:
                breaches.append(
                    f"Daily P&L loss {daily_pnl/nav:.2%} exceeds "
                    f"limit {self.limits.daily_pnl_stop:.1%}"
                )
            if weekly_pnl < 0 and abs(weekly_pnl / nav) > self.limits.weekly_pnl_stop:
                breaches.append(
                    f"Weekly P&L loss {weekly_pnl/nav:.2%} exceeds "
                    f"limit {self.limits.weekly_pnl_stop:.1%}"
                )
        return breaches
