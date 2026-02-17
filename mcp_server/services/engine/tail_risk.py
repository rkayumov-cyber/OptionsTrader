"""Tail risk and hedging framework (Section 8).

Hedge allocation, early warning signals, crisis protocol, 3-pillar tail signal.
"""

from mcp_server.engine_models import (
    EarlyWarningSignal,
    HedgeAllocation,
    HedgeInstrument,
    MarketInputs,
    TailRiskAssessment,
    TailTradingStatus,
)


class TailRiskManager:
    """Evaluates tail risk, manages hedge allocation, and monitors early warnings."""

    # Standing hedge allocation (Section 8.1)
    HEDGE_ALLOCATION = HedgeAllocation(
        annual_budget_pct=0.02,
        instruments=[
            HedgeInstrument(
                name="VIX Call Spreads",
                allocation=0.60,
                structure="buy VIX call at spot+4, sell at spot+12",
                tenor="30-60 DTE, roll monthly",
                rationale="3-5x convexity vs SPX puts in true crises [GS Hedging Toolkit]",
            ),
            HedgeInstrument(
                name="SPX Put Spreads",
                allocation=0.25,
                structure="buy 5% OTM put, sell 15% OTM put",
                tenor="90 DTE, roll quarterly",
                rationale="Better for moderate corrections (5-10%), Sharpe 0.88 [GS Asymmetric 27yr]",
            ),
            HedgeInstrument(
                name="Scheduled OTM Puts",
                allocation=0.15,
                structure="buy 5-10 delta SPX puts monthly",
                tenor="Monthly schedule",
                rationale="DCA into convexity > discretionary [GS Asymmetric 27yr]",
            ),
        ],
    )

    CRISIS_ACTIONS = [
        "Close ALL naked short vol immediately",
        "Reduce defined-risk short vol by 75%",
        "Deploy remaining hedge budget into convexity",
        "Cash position to minimum 40% of NAV",
        "Monitor for VIX peak (avg 2-4 weeks, avg peak ~45) [GS Vol Vitals]",
        "Do NOT sell vol until VIX establishes downtrend from peak",
    ]

    def assess(self, inputs: MarketInputs) -> TailRiskAssessment:
        """Run full tail risk assessment."""
        warnings = self._check_early_warnings(inputs)
        active_count = sum(1 for w in warnings if w.triggered)
        crisis = self._check_crisis(inputs, active_count)
        tail_trading = self._check_tail_signal(inputs)

        return TailRiskAssessment(
            hedge_allocation=self.HEDGE_ALLOCATION,
            early_warnings=warnings,
            active_warnings_count=active_count,
            crisis_protocol_active=crisis,
            crisis_actions=self.CRISIS_ACTIONS if crisis else [],
            tail_trading=tail_trading,
        )

    def _check_early_warnings(self, inputs: MarketInputs) -> list[EarlyWarningSignal]:
        warnings = []

        # Signal 1: HY OAS widening
        hy_triggered = inputs.credit.hy_oas_20d_change > 50
        warnings.append(EarlyWarningSignal(
            signal="HY OAS widens > 50bps in 20 days",
            action="Double hedge allocation",
            lead_time="2-4 weeks before equity vol spike [GS Equity Vol & Economy]",
            triggered=hy_triggered,
            current_value=inputs.credit.hy_oas_20d_change,
            threshold=50.0,
        ))

        # Signal 2: Bid-ask widening
        ba_triggered = inputs.liquidity.bid_ask_widening > 1.5
        warnings.append(EarlyWarningSignal(
            signal="Bid-ask spreads widen > 50% above 20d MA for > 10 days",
            action="Activate crisis protocol",
            lead_time="2-4 weeks [GS Rising Importance of Falling Liquidity]",
            triggered=ba_triggered,
            current_value=inputs.liquidity.bid_ask_widening,
            threshold=1.5,
        ))

        # Signal 3: Correlation spike
        corr_triggered = inputs.correlation.corr_pctile_1y > 80
        warnings.append(EarlyWarningSignal(
            signal="Implied correlation rises above 80th pctile in 5 days",
            action="Close all dispersion; review all short vol [JPM Equity Vol Strategy]",
            triggered=corr_triggered,
            current_value=inputs.correlation.corr_pctile_1y,
            threshold=80.0,
        ))

        # Signal 4: VVIX sustained elevation
        vvix_triggered = inputs.vol.vvix > 28
        warnings.append(EarlyWarningSignal(
            signal="VVIX > 28 sustained for 3+ days",
            action="Reduce all position sizes by 50% [GS Vol Vitals]",
            triggered=vvix_triggered,
            current_value=inputs.vol.vvix,
            threshold=28.0,
        ))

        return warnings

    def _check_crisis(self, inputs: MarketInputs, active_warnings: int) -> bool:
        """Crisis protocol triggers if VIX > 35 or multiple warnings fire."""
        if inputs.vol.vix > 35:
            return True
        if active_warnings >= 3:
            return True
        return False

    def _check_tail_signal(self, inputs: MarketInputs) -> TailTradingStatus:
        """Check 3-pillar tail trading signal (Section 8.2).

        Signal: 3M-1M implied vol term structure inversion (TS < 0).
        < 80 occurrences since 2004.
        """
        ts_value = inputs.term_structure.ts_1m_3m
        signal_active = ts_value < 0

        return TailTradingStatus(
            signal_active=signal_active,
            ts_value=ts_value,
            delta_pillar_active=signal_active,
            gamma_pillar_active=signal_active,
            vega_pillar_active=signal_active,
        )
