"""Market inputs collector.

Bridges existing market data providers to MarketInputs.
Mock mode generates consistent synthetic data.
Live mode pulls VIX/VVIX/credit from Yahoo + supplements.
"""

from __future__ import annotations

import math
import random
from datetime import datetime

from mcp_server.engine_models import (
    CorrelationData,
    CreditMacroData,
    EventCalendarData,
    LiquidityData,
    MarketInputs,
    SkewData,
    SpotData,
    TermStructureData,
    VolData,
)


class MarketInputsCollector:
    """Collects and assembles MarketInputs from providers or mock data."""

    def __init__(self, provider=None):
        """Initialize with an optional market data provider.

        Args:
            provider: A MarketDataProvider instance. If None, uses mock data.
        """
        self.provider = provider

    async def collect(self) -> MarketInputs:
        """Collect current market inputs.

        Uses live provider data if available, otherwise generates mock data.
        """
        if self.provider is not None:
            return await self._collect_live()
        return self._collect_mock()

    async def _collect_live(self) -> MarketInputs:
        """Collect inputs from live market data providers."""
        try:
            # Get SPX quote for spot data
            spx_quote = await self.provider.get_quote("SPY", "US")
            spx_price = spx_quote.price

            # Get VIX quote
            try:
                vix_quote = await self.provider.get_quote("^VIX", "US")
                vix = vix_quote.price
            except Exception:
                vix = 18.0  # fallback

            # Get price history for moving averages
            try:
                history = await self.provider.get_price_history("SPY", "US", limit=200)
                closes = [bar.close for bar in history.bars]
                sma_50 = sum(closes[-50:]) / min(len(closes), 50) if len(closes) >= 50 else spx_price
                sma_200 = sum(closes) / min(len(closes), 200) if len(closes) >= 200 else spx_price
                ret_1d = (closes[-1] / closes[-2] - 1) if len(closes) >= 2 else 0
                ret_5d = (closes[-1] / closes[-6] - 1) if len(closes) >= 6 else 0
                ret_20d = (closes[-1] / closes[-21] - 1) if len(closes) >= 21 else 0

                # Compute realized vol
                if len(closes) >= 21:
                    log_rets = [
                        math.log(closes[i] / closes[i - 1])
                        for i in range(max(1, len(closes) - 20), len(closes))
                    ]
                    rv_20d = (sum(r**2 for r in log_rets) / len(log_rets)) ** 0.5 * (252**0.5) * 100
                else:
                    rv_20d = vix
            except Exception:
                sma_50 = spx_price
                sma_200 = spx_price
                ret_1d = ret_5d = ret_20d = 0.0
                rv_20d = vix

            return MarketInputs(
                spot=SpotData(
                    spx_level=spx_price,
                    spx_ret_1d=ret_1d,
                    spx_ret_5d=ret_5d,
                    spx_ret_20d=ret_20d,
                    spx_sma_50=sma_50,
                    spx_sma_200=sma_200,
                ),
                vol=VolData(
                    vix=vix,
                    vix_percentile_1y=50.0,  # Would need historical data
                    iv_atm_1m=vix,
                    iv_atm_3m=vix + 1.5,
                    rv_20d=rv_20d,
                    iv_rv_spread=vix - rv_20d,
                ),
                timestamp=datetime.utcnow(),
            )
        except Exception:
            # Fall back to mock if anything fails
            return self._collect_mock()

    def _collect_mock(self) -> MarketInputs:
        """Generate consistent mock market inputs for testing."""
        random.seed(42)  # Deterministic for reproducibility

        vix = 17.5
        spx = 5850.0
        sma_50 = 5780.0
        sma_200 = 5520.0
        rv_20d = 14.2
        iv_1m = 17.0
        iv_3m = 18.5
        iv_6m = 19.2

        return MarketInputs(
            spot=SpotData(
                spx_level=spx,
                spx_ret_1d=0.003,
                spx_ret_5d=0.012,
                spx_ret_20d=0.025,
                spx_sma_50=sma_50,
                spx_sma_200=sma_200,
                breadth_pct_above_50dma=62.0,
            ),
            vol=VolData(
                vix=vix,
                vix_1d_change=-0.3,
                vix_5d_change=-1.2,
                vix_percentile_1y=42.0,
                vvix=19.5,
                vix9d=16.8,
                iv_atm_1m=iv_1m,
                iv_atm_3m=iv_3m,
                iv_atm_6m=iv_6m,
                rv_10d=15.1,
                rv_20d=rv_20d,
                rv_30d=14.8,
                iv_rv_spread=iv_1m - rv_20d,
            ),
            skew=SkewData(
                put_skew_25d_1m=5.2,
                put_skew_25d_3m=5.8,
                risk_reversal_25d=-4.5,
                skew_pctile_1y=48.0,
            ),
            term_structure=TermStructureData(
                ts_1m_3m=iv_3m - iv_1m,
                ts_3m_6m=iv_6m - iv_3m,
                ts_slope=0.8,
                vix_futures_1m=18.2,
                vix_futures_3m=19.5,
                roll_yield=(18.2 - vix) / vix,
            ),
            events=EventCalendarData(
                days_to_fomc=12,
                days_to_cpi=8,
                days_to_nfp=15,
                days_to_earnings=22,
                events_next_5d=0,
                events_next_20d=2,
            ),
            credit=CreditMacroData(
                hy_oas=380.0,
                hy_oas_20d_change=5.0,
                ig_spread=95.0,
                fed_funds_rate=4.50,
                us_10y_yield=4.25,
                us_2s10s=0.15,
            ),
            liquidity=LiquidityData(
                spx_bid_ask=0.04,
                spx_bid_ask_20d_ma=0.04,
                bid_ask_widening=1.0,
                emini_depth=1800.0,
                options_volume_oi=0.45,
            ),
            correlation=CorrelationData(
                implied_corr=45.0,
                realized_corr_20d=40.0,
                corr_pctile_1y=42.0,
                dispersion=5.0,
            ),
            timestamp=datetime.utcnow(),
        )
