"""Regime classifier (Section 1).

6-priority classification: Crisis > Liquidity Stress > Event > Vol Level > Trend > VVIX.
"""

from mcp_server.engine_models import (
    Confidence,
    EventType,
    MarketInputs,
    RegimeResult,
    Trend,
    VolRegime,
)

# Normal E-mini depth baseline (contracts) for liquidity comparison
NORMAL_EMINI_DEPTH = 1500.0


class RegimeClassifier:
    """Classifies the current market regime from input data."""

    def classify(self, inputs: MarketInputs) -> RegimeResult:
        """Run the full priority-ordered regime classification."""
        v = inputs.vol
        c = inputs.credit
        lq = inputs.liquidity
        s = inputs.spot
        sk = inputs.skew
        ts = inputs.term_structure
        ev = inputs.events

        # ── PRIORITY 1: CRISIS DETECTION ──
        crisis_signals = 0
        if v.vix > 30:
            crisis_signals += 2
        if v.vix_1d_change > 5:
            crisis_signals += 2
        if v.vix > 35:
            crisis_signals += 1
        if c.hy_oas_20d_change > 50:
            crisis_signals += 1
        if ts.ts_1m_3m < 0:
            crisis_signals += 1
        if lq.bid_ask_widening > 2.0:
            crisis_signals += 1

        if crisis_signals >= 3:
            return RegimeResult(
                regime=VolRegime.CRISIS,
                trend=self._classify_trend(s),
                confidence=Confidence.HIGH if crisis_signals >= 5 else Confidence.MEDIUM,
                confirming_signals=crisis_signals,
                actions=[
                    "CLOSE all naked short vol positions immediately",
                    "CLOSE all positions if VIX > 35 [GS Vol Vitals]",
                    "ONLY defined-risk spreads allowed (5-10 delta, 14-21 DTE)",
                    "Position size: 25% of baseline or FLAT",
                    "Activate tail hedges if not already on",
                    "Monitor for VIX peak (avg duration 2-4 weeks, avg peak ~45)",
                ],
            )

        # ── PRIORITY 2: LIQUIDITY STRESS ──
        liquidity_stress = 0
        if lq.bid_ask_widening > 1.5:
            liquidity_stress += 1
        if lq.spx_bid_ask > lq.spx_bid_ask_20d_ma * 1.3:
            liquidity_stress += 1
        if lq.emini_depth < 0.6 * NORMAL_EMINI_DEPTH:
            liquidity_stress += 1
        if c.hy_oas_20d_change > 30:
            liquidity_stress += 1

        if liquidity_stress >= 2:
            return RegimeResult(
                regime=VolRegime.LIQUIDITY_STRESS,
                trend=self._classify_trend(s),
                confidence=Confidence.MEDIUM,
                confirming_signals=liquidity_stress,
                actions=[
                    "REDUCE all positions by 25-50%",
                    "NO new naked short vol positions",
                    "Tighten stops on existing positions",
                    "Begin adding tail hedges (VIX call spreads)",
                    "Monitor: if persists >10 days, move to crisis protocol",
                ],
            )

        # ── PRIORITY 3: EVENT WINDOW ──
        event_active = False
        event_type = EventType.NONE

        if ev.days_to_fomc <= 5:
            event_active = True
            event_type = EventType.FOMC
        elif ev.days_to_cpi <= 3:
            event_active = True
            event_type = EventType.CPI
        elif ev.days_to_nfp <= 3:
            event_active = True
            event_type = EventType.NFP
        elif ev.days_to_earnings <= 3:
            event_active = True
            event_type = EventType.EARNINGS

        multi_event = ev.events_next_5d >= 2

        # ── PRIORITY 4: VOL LEVEL ──
        if v.vix < 12:
            vol_regime = VolRegime.VERY_LOW
        elif v.vix < 15:
            vol_regime = VolRegime.LOW
        elif v.vix < 20:
            vol_regime = VolRegime.NORMAL
        elif v.vix < 25:
            vol_regime = VolRegime.ELEVATED
        elif v.vix <= 30:
            vol_regime = VolRegime.HIGH
        else:
            vol_regime = VolRegime.EXTREME

        # ── PRIORITY 5: TREND ──
        trend = self._classify_trend(s)

        # ── PRIORITY 6: VVIX INSTABILITY ──
        vol_unstable = v.vvix > 22

        # ── CONFIDENCE SCORING ──
        confirming = self._score_confidence(vol_regime, v, sk, ts, c)
        if confirming >= 3:
            confidence = Confidence.HIGH
        elif confirming >= 2:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW

        # ── BUILD ACTIONS ──
        actions = self._build_actions(vol_regime, trend, event_active, vol_unstable)

        return RegimeResult(
            regime=vol_regime,
            trend=trend,
            event_active=event_active,
            event_type=event_type,
            multi_event=multi_event,
            vol_unstable=vol_unstable,
            confidence=confidence,
            confirming_signals=confirming,
            actions=actions,
        )

    @staticmethod
    def _classify_trend(s) -> Trend:
        if s.spx_level > s.spx_sma_50 and s.spx_level > s.spx_sma_200:
            if s.breadth_pct_above_50dma > 60:
                return Trend.STRONG_UPTREND
            return Trend.UPTREND
        if s.spx_level < s.spx_sma_50 and s.spx_level < s.spx_sma_200:
            if s.breadth_pct_above_50dma < 40:
                return Trend.STRONG_DOWNTREND
            return Trend.DOWNTREND
        return Trend.RANGE_BOUND

    @staticmethod
    def _score_confidence(vol_regime, v, sk, ts, c) -> int:
        confirming = 0
        # IV-RV agreement
        if vol_regime in (VolRegime.LOW, VolRegime.VERY_LOW) and v.iv_rv_spread < 2:
            confirming += 1
        elif vol_regime in (VolRegime.ELEVATED, VolRegime.HIGH) and v.iv_rv_spread > 3:
            confirming += 1
        # Skew alignment
        if vol_regime in (VolRegime.ELEVATED, VolRegime.HIGH) and sk.put_skew_25d_1m > 6:
            confirming += 1
        elif vol_regime in (VolRegime.LOW, VolRegime.VERY_LOW) and sk.put_skew_25d_1m < 4:
            confirming += 1
        # Term structure alignment
        if vol_regime in (VolRegime.LOW, VolRegime.NORMAL) and ts.ts_1m_3m > 0:
            confirming += 1
        elif vol_regime == VolRegime.HIGH and ts.ts_1m_3m < 1:
            confirming += 1
        # Credit confirmation
        if vol_regime in (VolRegime.LOW, VolRegime.NORMAL) and c.hy_oas_20d_change < 20:
            confirming += 1
        elif vol_regime in (VolRegime.ELEVATED, VolRegime.HIGH) and c.hy_oas_20d_change > 30:
            confirming += 1
        return confirming

    @staticmethod
    def _build_actions(vol_regime, trend, event_active, vol_unstable) -> list[str]:
        actions = []
        if vol_regime == VolRegime.VERY_LOW:
            actions.append("Maximize premium selling at full size")
            actions.append("Cheap convexity available - consider tail hedges")
        elif vol_regime == VolRegime.LOW:
            actions.append("Full premium selling allowed")
            actions.append("Begin building convexity positions")
        elif vol_regime == VolRegime.NORMAL:
            actions.append("Standard position sizes, balanced approach")
        elif vol_regime == VolRegime.ELEVATED:
            actions.append("Reduce selling to 50% size; defined-risk only for new trades")
            actions.append("Review all naked positions for rolling/closing")
        elif vol_regime == VolRegime.HIGH:
            actions.append("Only defined-risk spreads at 25% size")
            actions.append("Consider long convexity positions")
        elif vol_regime == VolRegime.EXTREME:
            actions.append("No premium selling")
            actions.append("Buy convexity only; activate crisis protocol")

        if event_active:
            actions.append("Event window active - use event playbook")
        if vol_unstable:
            actions.append("VVIX > 22: vol surface unstable, reduce sizes 25-50%")

        if trend in (Trend.STRONG_DOWNTREND, Trend.DOWNTREND):
            actions.append("Downtrend: favor bearish strategies, tighten upside")
        elif trend in (Trend.STRONG_UPTREND, Trend.UPTREND):
            actions.append("Uptrend: favor bullish strategies, maintain hedges")

        return actions
