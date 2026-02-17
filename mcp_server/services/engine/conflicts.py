"""Conflict resolution matrix (Section 10).

8 conflict scenarios with detection and resolution rules.
"""

from mcp_server.engine_models import (
    ConflictScenario,
    MarketInputs,
    RegimeResult,
    VolRegime,
)


# ── Conflict Definitions ─────────────────────────────────────────────────

CONFLICT_DEFINITIONS: list[dict] = [
    {
        "conflict_id": "C1",
        "description": "IV says sell, Trend says caution",
        "signal_a": "IV Rank > 75",
        "signal_b": "SPX below 200 DMA",
        "resolution": "Defined-risk spreads only. 50% size. No naked short.",
    },
    {
        "conflict_id": "C2",
        "description": "Event approaching, carry attractive",
        "signal_a": "Theta > 0 carry setup",
        "signal_b": "FOMC/CPI in 3 days",
        "resolution": "WAIT. Enter T+1 post-event. IV crush creates better entry.",
    },
    {
        "conflict_id": "C3",
        "description": "Low vol + Steep skew",
        "signal_a": "VIX < 15",
        "signal_b": "25d skew > 80th pctile",
        "resolution": "Risk reversals or put ladders to monetize skew. No naked short puts.",
    },
    {
        "conflict_id": "C4",
        "description": "Credit widening, VIX still low",
        "signal_a": "HY OAS +50bps / 20d",
        "signal_b": "VIX < 18",
        "resolution": "Reduce short vol 25%. Add VIX call spread. Credit leads equity vol 2-4 weeks.",
    },
    {
        "conflict_id": "C5",
        "description": "Dispersion high, correlation low",
        "signal_a": "Implied corr < 30th pctile",
        "signal_b": "Sector dispersion elevated",
        "resolution": "Enter dispersion trade at 50% standard size. Defined risk preferred.",
    },
    {
        "conflict_id": "C6",
        "description": "Regime confidence = LOW",
        "signal_a": "Mixed signals",
        "signal_b": "No clear regime",
        "resolution": "Defined-risk only. 50% size. No new naked positions. WAIT for clarity.",
    },
    {
        "conflict_id": "C7",
        "description": "VVIX elevated, VIX normal",
        "signal_a": "VVIX > 22",
        "signal_b": "VIX 15-20",
        "resolution": "Vol surface unstable. Reduce all sizes 25-50%. Avoid long-dated vega.",
    },
    {
        "conflict_id": "C8",
        "description": "Term structure inverted",
        "signal_a": "1M IV > 3M IV",
        "signal_b": "VIX < 25",
        "resolution": "Activate tail trading framework (3-pillar). This is the signal.",
    },
]


class ConflictResolver:
    """Detects and resolves conflicting market signals."""

    def check_conflicts(
        self, regime: RegimeResult, inputs: MarketInputs
    ) -> list[ConflictScenario]:
        """Check all 8 conflict scenarios against current market state.

        Returns only detected conflicts with their resolutions.
        """
        all_conflicts = self._evaluate_all(regime, inputs)
        return [c for c in all_conflicts if c.detected]

    def check_all(
        self, regime: RegimeResult, inputs: MarketInputs
    ) -> list[ConflictScenario]:
        """Return all conflict scenarios with detection status."""
        return self._evaluate_all(regime, inputs)

    def _evaluate_all(
        self, regime: RegimeResult, inputs: MarketInputs
    ) -> list[ConflictScenario]:
        results = []
        v = inputs.vol
        s = inputs.spot
        c = inputs.credit
        ev = inputs.events
        sk = inputs.skew
        co = inputs.correlation
        ts = inputs.term_structure

        # C1: IV says sell, Trend says caution
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[0],
            detected=(v.vix_percentile_1y > 75 and s.spx_level < s.spx_sma_200),
        ))

        # C2: Event approaching, carry attractive
        near_event = min(ev.days_to_fomc, ev.days_to_cpi, ev.days_to_nfp) <= 3
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[1],
            detected=(near_event and v.vix_percentile_1y > 40),
        ))

        # C3: Low vol + Steep skew
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[2],
            detected=(v.vix < 15 and sk.skew_pctile_1y > 80),
        ))

        # C4: Credit widening, VIX still low
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[3],
            detected=(c.hy_oas_20d_change > 50 and v.vix < 18),
        ))

        # C5: Dispersion high, correlation low
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[4],
            detected=(co.corr_pctile_1y < 30 and co.dispersion > 10),
        ))

        # C6: Regime confidence = LOW
        from mcp_server.engine_models import Confidence
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[5],
            detected=(regime.confidence == Confidence.LOW),
        ))

        # C7: VVIX elevated, VIX normal
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[6],
            detected=(v.vvix > 22 and 15 <= v.vix <= 20),
        ))

        # C8: Term structure inverted
        results.append(ConflictScenario(
            **CONFLICT_DEFINITIONS[7],
            detected=(ts.ts_1m_3m < 0 and v.vix < 25),
        ))

        return results
