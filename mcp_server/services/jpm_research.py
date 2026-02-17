"""JPM Volatility Research Service.

Provides access to J.P. Morgan US Single Stock Volatility Chartbook data.
Data sourced from the January 6, 2026 report.
"""

from datetime import date, datetime
from typing import Literal

from mcp_server.models import (
    JPMTradingCandidate,
    JPMVolatilityScreen,
    JPMStockData,
    JPMReportMetadata,
    JPMResearchData,
    JPMStrategyType,
    JPMScreenType,
)


class JPMResearchService:
    """Service for JPM volatility research data.

    Data sourced from J.P. Morgan US Single Stock Volatility Chartbook
    dated January 6, 2026.
    """

    def __init__(self):
        """Initialize with data from JPM report dated Jan 6, 2026."""
        self._report_date = date(2026, 1, 6)
        self._load_data()

    def _load_data(self):
        """Load JPM research data from the January 6, 2026 report."""
        # ============================================================
        # CALL OVERWRITING CANDIDATES (Attractive 3M 105% Call Overwriting)
        # Triggered when: sell signals > buy signals AND vol rich signals > vol cheap signals
        # ============================================================
        self._call_overwriting = [
            JPMTradingCandidate(
                ticker="GE",
                strategy="call_overwriting",
                iv30=29.2,
                iv_percentile=82,
                hv30=22.5,
                iv_hv_spread=6.7,
                skew=-2.1,
                rationale="1M +10.9%, RSI 66.7, IV/RV %ile 82 vs S&P. JPM OW rating. 3M 105 Call premium 4.1%. Earnings Jan 22.",
            ),
            JPMTradingCandidate(
                ticker="TGT",
                strategy="call_overwriting",
                iv30=37.7,
                iv_percentile=96,
                hv30=31.0,
                iv_hv_spread=6.7,
                skew=-1.8,
                rationale="1M +11.1%, RSI 67.1, IV/RV %ile 96 vs S&P. Neutral rating. 3M 105 Call premium 5.4%. Earnings Mar 4.",
            ),
            JPMTradingCandidate(
                ticker="FDX",
                strategy="call_overwriting",
                iv30=27.5,
                iv_percentile=85,
                hv30=22.0,
                iv_hv_spread=5.5,
                skew=-2.3,
                rationale="1M +8.4%, RSI 70.3, IV/RV %ile 85. Neutral rating. 3M 105 Call premium 3.6%. Earnings Mar 19.",
            ),
            JPMTradingCandidate(
                ticker="AGNC",
                strategy="call_overwriting",
                iv30=19.1,
                iv_percentile=77,
                hv30=15.2,
                iv_hv_spread=3.9,
                skew=-1.5,
                rationale="1M +4.5%, RSI 70.5, IV/RV %ile 77 vs S&P. JPM OW rating. 3M 105 Call premium 1.2%.",
            ),
            JPMTradingCandidate(
                ticker="MS",
                strategy="call_overwriting",
                iv30=26.7,
                iv_percentile=87,
                hv30=24.7,
                iv_hv_spread=2.0,
                skew=-1.7,
                rationale="1M +7.6%, RSI 69.1, IV/RV %ile 87 vs S&P. Neutral rating. 3M 105 Call premium 3.4%. Earnings Jan 15.",
            ),
            JPMTradingCandidate(
                ticker="C",
                strategy="call_overwriting",
                iv30=29.0,
                iv_percentile=89,
                hv30=25.5,
                iv_hv_spread=3.5,
                skew=-1.9,
                rationale="1M +15.0%, RSI 74.7, IV/RV %ile 89, sector rel 97. JPM OW with 9.5% upside. Earnings Jan 14.",
            ),
            JPMTradingCandidate(
                ticker="ABNB",
                strategy="call_overwriting",
                iv30=32.1,
                iv_percentile=98,
                hv30=25.0,
                iv_hv_spread=7.1,
                skew=-2.0,
                rationale="1M +12.2%, RSI 64.7, IV/RV %ile 98, sector rel 100. Neutral rating. Premium 4.7%. Earnings Feb 13.",
            ),
            JPMTradingCandidate(
                ticker="SYF",
                strategy="call_overwriting",
                iv30=29.1,
                iv_percentile=81,
                hv30=24.5,
                iv_hv_spread=4.6,
                skew=-1.6,
                rationale="1M +7.3%, RSI 67.7, IV/RV %ile 81. Neutral rating. 3M 105 Call premium 4.0%. Earnings Jan 28.",
            ),
            JPMTradingCandidate(
                ticker="XOM",
                strategy="call_overwriting",
                iv30=19.9,
                iv_percentile=52,
                hv30=17.1,
                iv_hv_spread=2.8,
                skew=-1.4,
                rationale="1M +6.3%, RSI 70.6, beta adj +6.0%. JPM OW rating. 3M 105 Call premium 2.1%. Earnings Jan 30.",
            ),
            JPMTradingCandidate(
                ticker="JNJ",
                strategy="call_overwriting",
                iv30=19.2,
                iv_percentile=93,
                hv30=15.8,
                iv_hv_spread=3.4,
                skew=-1.1,
                rationale="1M +0.9%, RSI 47.6, but IV/RV %ile 93, sector rel 98. Neutral rating. Premium 2.0%. Earnings Jan 21.",
            ),
        ]

        # ============================================================
        # CALL BUYING CANDIDATES (Attractive 3M 105% Call Buying)
        # Triggered when: buy signals > sell signals AND vol cheap signals > vol rich signals
        # ============================================================
        self._call_buying = [
            JPMTradingCandidate(
                ticker="DDOG",
                strategy="call_buying",
                iv30=46.0,
                iv_percentile=6,
                hv30=57.0,
                iv_hv_spread=-11.0,
                skew=-0.8,
                rationale="1M -14.5%, RSI 27.4, IV/RV %ile only 6. JPM OW with 49.5% price upside. Cheap vol for bullish bet.",
            ),
            JPMTradingCandidate(
                ticker="DOCU",
                strategy="call_buying",
                iv30=40.7,
                iv_percentile=22,
                hv30=37.6,
                iv_hv_spread=3.1,
                skew=-1.2,
                rationale="1M -5.8%, RSI 36.4, IV/RV %ile 22, sector rel 15. Neutral rating with 20.3% upside. Earnings Mar 13.",
            ),
            JPMTradingCandidate(
                ticker="AVGO",
                strategy="call_buying",
                iv30=47.6,
                iv_percentile=14,
                hv30=54.3,
                iv_hv_spread=-6.7,
                skew=-0.5,
                rationale="1M -8.9%, RSI 42.8, IV/RV %ile 14, sector rel 12. JPM OW with 36.6% upside. AI tailwinds. Earnings Mar 6.",
            ),
            JPMTradingCandidate(
                ticker="SNOW",
                strategy="call_buying",
                iv30=45.2,
                iv_percentile=8,
                hv30=42.3,
                iv_hv_spread=2.9,
                skew=-0.7,
                rationale="1M -16.5%, RSI 46.0, IV/RV %ile 8, sector rel 10. JPM OW with 23.7% upside. Cloud growth story.",
            ),
            JPMTradingCandidate(
                ticker="PSTG",
                strategy="call_buying",
                iv30=54.4,
                iv_percentile=1,
                hv30=82.1,
                iv_hv_spread=-27.7,
                skew=-0.9,
                rationale="1M -27.1%, RSI 44.3, IV/RV %ile just 1! JPM OW with 52.2% upside. Extremely cheap vol.",
            ),
            JPMTradingCandidate(
                ticker="PEP",
                strategy="call_buying",
                iv30=19.4,
                iv_percentile=30,
                hv30=17.5,
                iv_hv_spread=1.9,
                skew=-0.4,
                rationale="1M -4.3%, RSI 29.9, IV/RV %ile 30, sector rel 22. JPM OW with 15.3% upside. Defensive quality.",
            ),
            JPMTradingCandidate(
                ticker="PSX",
                strategy="call_buying",
                iv30=28.4,
                iv_percentile=26,
                hv30=25.0,
                iv_hv_spread=3.4,
                skew=-0.6,
                rationale="1M -5.1%, RSI 62.5, IV/RV %ile 26, sector rel 24. JPM OW with 17.9% upside. Earnings Feb 4.",
            ),
            JPMTradingCandidate(
                ticker="ALL",
                strategy="call_buying",
                iv30=20.2,
                iv_percentile=27,
                hv30=18.0,
                iv_hv_spread=2.2,
                skew=-0.3,
                rationale="1M -2.4%, RSI 47.0, IV/RV %ile 27, sector rel 20. JPM OW with 27.6% upside. Best EPS +5.9%. Earnings Feb 4.",
            ),
            JPMTradingCandidate(
                ticker="WYNN",
                strategy="call_buying",
                iv30=33.6,
                iv_percentile=16,
                hv30=30.5,
                iv_hv_spread=3.1,
                skew=-0.5,
                rationale="1M -7.9%, RSI 40.1, IV/RV %ile 16, sector rel 28. JPM OW with 18.3% upside. Gaming recovery.",
            ),
            JPMTradingCandidate(
                ticker="CPB",
                strategy="call_buying",
                iv30=26.9,
                iv_percentile=10,
                hv30=25.6,
                iv_hv_spread=1.3,
                skew=-0.4,
                rationale="1M -7.3%, RSI 27.1, IV/RV %ile 10, sector rel 9. Neutral with 11.9% upside. Ex-div Jan 8. Earnings Mar 5.",
            ),
        ]

        # ============================================================
        # PUT UNDERWRITING CANDIDATES (Attractive 3M 95% Put Underwriting)
        # Triggered when: buy signals > sell signals AND vol rich signals > vol cheap signals
        # ============================================================
        self._put_underwriting = [
            JPMTradingCandidate(
                ticker="AAP",
                strategy="put_underwriting",
                iv30=64.6,
                iv_percentile=91,
                hv30=53.6,
                iv_hv_spread=11.0,
                skew=3.2,
                rationale="1M -26.2%, RSI 28.8, but IV/RV %ile 91, sector rel 90. Neutral with 59.4% upside. Rich premium for CSP.",
            ),
            JPMTradingCandidate(
                ticker="COST",
                strategy="put_underwriting",
                iv30=23.2,
                iv_percentile=87,
                hv30=18.3,
                iv_hv_spread=4.9,
                skew=1.8,
                rationale="1M -7.3%, RSI 49.1, IV/RV %ile 87, sector rel 91. JPM OW with 20.2% upside. Quality premium collection.",
            ),
            JPMTradingCandidate(
                ticker="INTU",
                strategy="put_underwriting",
                iv30=31.8,
                iv_percentile=89,
                hv30=26.1,
                iv_hv_spread=5.7,
                skew=2.1,
                rationale="1M -1.0%, RSI 37.8, IV/RV %ile 89, sector rel 90. JPM OW with 19.1% upside. 3M 95 Put premium 3.7%.",
            ),
            JPMTradingCandidate(
                ticker="ORLY",
                strategy="put_underwriting",
                iv30=26.9,
                iv_percentile=95,
                hv30=20.5,
                iv_hv_spread=6.4,
                skew=1.9,
                rationale="1M -9.5%, RSI 32.0, IV/RV %ile 95, sector rel 96. JPM OW with 26.2% upside. Premium 2.7%.",
            ),
            JPMTradingCandidate(
                ticker="PANW",
                strategy="put_underwriting",
                iv30=35.3,
                iv_percentile=91,
                hv30=28.9,
                iv_hv_spread=6.4,
                skew=2.0,
                rationale="1M -5.5%, RSI 38.2, IV/RV %ile 91, sector rel 92. JPM OW with 31.0% upside. Premium 4.2%. Earnings Feb 13.",
            ),
            JPMTradingCandidate(
                ticker="ADSK",
                strategy="put_underwriting",
                iv30=29.7,
                iv_percentile=77,
                hv30=24.2,
                iv_hv_spread=5.5,
                skew=1.7,
                rationale="1M -7.6%, RSI 37.1, IV/RV %ile 77, sector rel 78. Neutral with 11.3% upside. Premium 3.2%.",
            ),
            JPMTradingCandidate(
                ticker="LNG",
                strategy="put_underwriting",
                iv30=28.9,
                iv_percentile=100,
                hv30=17.1,
                iv_hv_spread=11.8,
                skew=2.5,
                rationale="1M -5.5%, RSI 53.2, IV/RV %ile 100 (richest!), sector rel 100. JPM OW with 44.6% upside. Premium 3.2%.",
            ),
            JPMTradingCandidate(
                ticker="TTD",
                strategy="put_underwriting",
                iv30=62.4,
                iv_percentile=98,
                hv30=39.9,
                iv_hv_spread=22.5,
                skew=3.0,
                rationale="1M -5.7%, RSI 56.7, IV/RV %ile 98, sector rel 81. Unrated with 59.2% upside. Very rich premium 9.2%.",
            ),
            JPMTradingCandidate(
                ticker="PAYC",
                strategy="put_underwriting",
                iv30=40.8,
                iv_percentile=78,
                hv30=35.7,
                iv_hv_spread=5.1,
                skew=1.8,
                rationale="1M -5.9%, RSI 31.7, IV/RV %ile 78, sector rel 80. Neutral with 44.4% upside. Premium 5.3%.",
            ),
            JPMTradingCandidate(
                ticker="PHM",
                strategy="put_underwriting",
                iv30=34.1,
                iv_percentile=79,
                hv30=28.0,
                iv_hv_spread=6.1,
                skew=1.6,
                rationale="1M -5.9%, RSI 46.0, IV/RV %ile 79, sector rel 82. JPM OW with 25.1% upside. Premium 4.1%. Earnings Jan 29.",
            ),
        ]

        # ============================================================
        # PUT BUYING CANDIDATES (Attractive 3M 95% Put Buying)
        # Triggered when: sell signals > buy signals AND vol cheap signals > vol rich signals
        # ============================================================
        self._put_buying = [
            JPMTradingCandidate(
                ticker="CNC",
                strategy="put_buying",
                iv30=45.9,
                iv_percentile=11,
                hv30=50.0,
                iv_hv_spread=-4.1,
                skew=0.5,
                rationale="1M +7.7%, RSI 75.7, but IV/RV %ile only 11, sector rel 20. Neutral with -9.0% downside. Cheap protection.",
            ),
            JPMTradingCandidate(
                ticker="HAL",
                strategy="put_buying",
                iv30=36.6,
                iv_percentile=12,
                hv30=42.1,
                iv_hv_spread=-5.5,
                skew=0.8,
                rationale="1M +10.0%, RSI 76.8, IV/RV %ile 12, sector rel 0 (cheapest in sector!). OW but extended. Earnings Jan 21.",
            ),
            JPMTradingCandidate(
                ticker="ULTA",
                strategy="put_buying",
                iv30=32.4,
                iv_percentile=13,
                hv30=35.0,
                iv_hv_spread=-2.6,
                skew=0.4,
                rationale="1M +13.1%, RSI 71.0, IV/RV %ile 13, sector rel 21. JPM OW but overbought. Cheap downside protection.",
            ),
            JPMTradingCandidate(
                ticker="FCX",
                strategy="put_buying",
                iv30=39.4,
                iv_percentile=2,
                hv30=37.0,
                iv_hv_spread=2.4,
                skew=0.6,
                rationale="1M +20.9%, RSI 76.2, IV/RV %ile just 2, sector rel 0. JPM OW but extremely overbought. Cheap vol. Earnings Jan 23.",
            ),
            JPMTradingCandidate(
                ticker="COP",
                strategy="put_buying",
                iv30=28.2,
                iv_percentile=16,
                hv30=29.6,
                iv_hv_spread=-1.4,
                skew=0.5,
                rationale="1M +8.3%, RSI 66.0, IV/RV %ile 16, sector rel 12. JPM OW. Cheap hedging opportunity. Earnings Feb 5.",
            ),
            JPMTradingCandidate(
                ticker="EXPE",
                strategy="put_buying",
                iv30=41.4,
                iv_percentile=12,
                hv30=45.0,
                iv_hv_spread=-3.6,
                skew=0.4,
                rationale="1M +7.3%, RSI 64.3, IV/RV %ile 12, sector rel 19. Neutral with -8.1% downside target. Earnings Feb 6.",
            ),
            JPMTradingCandidate(
                ticker="BURL",
                strategy="put_buying",
                iv30=40.1,
                iv_percentile=10,
                hv30=47.5,
                iv_hv_spread=-7.4,
                skew=0.3,
                rationale="1M +21.8%, RSI 68.3, IV/RV %ile 10, sector rel 15. JPM OW but very extended. Cheap protection.",
            ),
            JPMTradingCandidate(
                ticker="KMX",
                strategy="put_buying",
                iv30=48.4,
                iv_percentile=1,
                hv30=60.0,
                iv_hv_spread=-11.6,
                skew=0.7,
                rationale="1M +1.5%, RSI 56.5, IV/RV %ile just 1. UW rating with -28.7% target. Extremely cheap vol for bearish bet.",
            ),
            JPMTradingCandidate(
                ticker="SCCO",
                strategy="put_buying",
                iv30=39.6,
                iv_percentile=21,
                hv30=42.0,
                iv_hv_spread=-2.4,
                skew=0.5,
                rationale="1M +10.2%, RSI 67.9, IV/RV %ile 21, sector rel 24. Neutral with -19.6% target. Copper pullback hedge.",
            ),
            JPMTradingCandidate(
                ticker="AA",
                strategy="put_buying",
                iv30=53.2,
                iv_percentile=24,
                hv30=58.0,
                iv_hv_spread=-4.8,
                skew=0.6,
                rationale="1M +36.4%, RSI 82.7 (very overbought!), IV/RV %ile 24, sector rel 35. Neutral with -20.4% target. Earnings Jan 22.",
            ),
        ]

        # ============================================================
        # VOLATILITY SCREENS - RICH IV (Volatility Score > 75%)
        # ============================================================
        self._rich_iv = [
            JPMVolatilityScreen(ticker="LNG", screen_type="rich_iv", iv30=28.5, iv_percentile=100, hv30=17.1, iv_change_1w=0.5, price_change_1m=-5.5),
            JPMVolatilityScreen(ticker="NSC", screen_type="rich_iv", iv30=21.8, iv_percentile=99, hv30=13.7, iv_change_1w=2.0, price_change_1m=-1.3),
            JPMVolatilityScreen(ticker="ABNB", screen_type="rich_iv", iv30=33.1, iv_percentile=98, hv30=25.0, iv_change_1w=0.6, price_change_1m=12.2),
            JPMVolatilityScreen(ticker="OKTA", screen_type="rich_iv", iv30=43.6, iv_percentile=97, hv30=31.1, iv_change_1w=0.3, price_change_1m=2.2),
            JPMVolatilityScreen(ticker="EW", screen_type="rich_iv", iv30=28.0, iv_percentile=95, hv30=22.9, iv_change_1w=0.4, price_change_1m=0.7),
            JPMVolatilityScreen(ticker="FTNT", screen_type="rich_iv", iv30=37.5, iv_percentile=97, hv30=28.3, iv_change_1w=-0.9, price_change_1m=-6.1),
            JPMVolatilityScreen(ticker="CAR", screen_type="rich_iv", iv30=49.3, iv_percentile=98, hv30=38.7, iv_change_1w=1.4, price_change_1m=-2.8),
            JPMVolatilityScreen(ticker="TGT", screen_type="rich_iv", iv30=38.4, iv_percentile=96, hv30=31.0, iv_change_1w=-0.3, price_change_1m=11.1),
            JPMVolatilityScreen(ticker="SMG", screen_type="rich_iv", iv30=37.4, iv_percentile=94, hv30=29.7, iv_change_1w=-1.6, price_change_1m=6.9),
            JPMVolatilityScreen(ticker="TEAM", screen_type="rich_iv", iv30=52.6, iv_percentile=97, hv30=38.3, iv_change_1w=0.6, price_change_1m=0.6),
            JPMVolatilityScreen(ticker="TJX", screen_type="rich_iv", iv30=20.4, iv_percentile=96, hv30=15.4, iv_change_1w=-0.3, price_change_1m=2.8),
            JPMVolatilityScreen(ticker="BK", screen_type="rich_iv", iv30=23.8, iv_percentile=92, hv30=19.6, iv_change_1w=-0.8, price_change_1m=4.4),
            JPMVolatilityScreen(ticker="CLX", screen_type="rich_iv", iv30=30.7, iv_percentile=92, hv30=23.5, iv_change_1w=0.1, price_change_1m=-4.8),
            JPMVolatilityScreen(ticker="JNJ", screen_type="rich_iv", iv30=20.2, iv_percentile=93, hv30=15.8, iv_change_1w=0.3, price_change_1m=0.9),
            JPMVolatilityScreen(ticker="MSFT", screen_type="rich_iv", iv30=25.2, iv_percentile=96, hv30=19.8, iv_change_1w=0.7, price_change_1m=-3.5),
        ]

        # ============================================================
        # VOLATILITY SCREENS - CHEAP IV (Volatility Score < 25%)
        # ============================================================
        self._cheap_iv = [
            JPMVolatilityScreen(ticker="CI", screen_type="cheap_iv", iv30=31.5, iv_percentile=1, hv30=49.3, iv_change_1w=-0.2, price_change_1m=1.8),
            JPMVolatilityScreen(ticker="JBHT", screen_type="cheap_iv", iv30=33.7, iv_percentile=2, hv30=49.0, iv_change_1w=2.2, price_change_1m=5.9),
            JPMVolatilityScreen(ticker="FCX", screen_type="cheap_iv", iv30=39.8, iv_percentile=2, hv30=37.0, iv_change_1w=0.2, price_change_1m=20.9),
            JPMVolatilityScreen(ticker="ORCL", screen_type="cheap_iv", iv30=51.3, iv_percentile=1, hv30=52.9, iv_change_1w=1.4, price_change_1m=-2.7),
            JPMVolatilityScreen(ticker="KSS", screen_type="cheap_iv", iv30=65.8, iv_percentile=2, hv30=94.1, iv_change_1w=-1.5, price_change_1m=-13.6),
            JPMVolatilityScreen(ticker="BBWI", screen_type="cheap_iv", iv30=53.6, iv_percentile=3, hv30=75.5, iv_change_1w=-0.9, price_change_1m=11.5),
            JPMVolatilityScreen(ticker="ILMN", screen_type="cheap_iv", iv30=43.8, iv_percentile=3, hv30=57.3, iv_change_1w=-0.5, price_change_1m=5.3),
            JPMVolatilityScreen(ticker="AMD", screen_type="cheap_iv", iv30=53.2, iv_percentile=4, hv30=58.0, iv_change_1w=2.4, price_change_1m=3.8),
            JPMVolatilityScreen(ticker="CHRW", screen_type="cheap_iv", iv30=32.3, iv_percentile=6, hv30=43.8, iv_change_1w=-0.9, price_change_1m=2.6),
            JPMVolatilityScreen(ticker="QS", screen_type="cheap_iv", iv30=85.5, iv_percentile=4, hv30=96.2, iv_change_1w=0.1, price_change_1m=-9.1),
            JPMVolatilityScreen(ticker="PFE", screen_type="cheap_iv", iv30=22.7, iv_percentile=4, hv30=22.4, iv_change_1w=0.6, price_change_1m=0.1),
            JPMVolatilityScreen(ticker="INTC", screen_type="cheap_iv", iv30=53.9, iv_percentile=6, hv30=52.9, iv_change_1w=2.6, price_change_1m=-9.4),
            JPMVolatilityScreen(ticker="HAL", screen_type="cheap_iv", iv30=36.9, iv_percentile=12, hv30=42.1, iv_change_1w=3.1, price_change_1m=10.0),
            JPMVolatilityScreen(ticker="DDOG", screen_type="cheap_iv", iv30=46.6, iv_percentile=6, hv30=57.0, iv_change_1w=1.6, price_change_1m=-14.5),
            JPMVolatilityScreen(ticker="SNOW", screen_type="cheap_iv", iv30=46.0, iv_percentile=8, hv30=42.3, iv_change_1w=0.5, price_change_1m=-16.5),
        ]

        # ============================================================
        # IV TOP MOVERS (Largest 1-week IV point increases)
        # ============================================================
        self._iv_top_movers = [
            JPMVolatilityScreen(ticker="BILL", screen_type="iv_top_movers", iv30=57.8, iv_percentile=55, hv30=43.8, iv_change_1w=7.8, price_change_1m=-8.4),
            JPMVolatilityScreen(ticker="WOLF", screen_type="iv_top_movers", iv30=109.5, iv_percentile=24, hv30=87.7, iv_change_1w=5.1, price_change_1m=9.4),
            JPMVolatilityScreen(ticker="PTON", screen_type="iv_top_movers", iv30=64.9, iv_percentile=70, hv30=52.8, iv_change_1w=5.0, price_change_1m=-2.4),
            JPMVolatilityScreen(ticker="AAP", screen_type="iv_top_movers", iv30=66.7, iv_percentile=91, hv30=53.6, iv_change_1w=3.4, price_change_1m=-2.5),
            JPMVolatilityScreen(ticker="COIN", screen_type="iv_top_movers", iv30=58.4, iv_percentile=22, hv30=63.8, iv_change_1w=3.2, price_change_1m=1.2),
            JPMVolatilityScreen(ticker="PINS", screen_type="iv_top_movers", iv30=52.4, iv_percentile=21, hv30=62.4, iv_change_1w=3.1, price_change_1m=2.6),
            JPMVolatilityScreen(ticker="HAL", screen_type="iv_top_movers", iv30=36.9, iv_percentile=12, hv30=42.1, iv_change_1w=3.1, price_change_1m=5.2),
            JPMVolatilityScreen(ticker="LRCX", screen_type="iv_top_movers", iv30=53.3, iv_percentile=43, hv30=52.5, iv_change_1w=2.7, price_change_1m=5.2),
            JPMVolatilityScreen(ticker="MPW", screen_type="iv_top_movers", iv30=37.6, iv_percentile=17, hv30=36.1, iv_change_1w=2.7, price_change_1m=-0.2),
            JPMVolatilityScreen(ticker="PLUG", screen_type="iv_top_movers", iv30=101.7, iv_percentile=9, hv30=88.3, iv_change_1w=2.7, price_change_1m=13.2),
        ]

        # ============================================================
        # IV BOTTOM MOVERS (Largest 1-week IV point decreases)
        # ============================================================
        self._iv_bottom_movers = [
            JPMVolatilityScreen(ticker="ELV", screen_type="iv_bottom_movers", iv30=33.6, iv_percentile=62, hv30=29.2, iv_change_1w=-2.3, price_change_1m=1.7),
            JPMVolatilityScreen(ticker="RBLX", screen_type="iv_bottom_movers", iv30=57.9, iv_percentile=74, hv30=51.5, iv_change_1w=-2.2, price_change_1m=-0.7),
            JPMVolatilityScreen(ticker="THC", screen_type="iv_bottom_movers", iv30=36.3, iv_percentile=32, hv30=38.1, iv_change_1w=-2.1, price_change_1m=-0.8),
            JPMVolatilityScreen(ticker="MRNA", screen_type="iv_bottom_movers", iv30=66.7, iv_percentile=43, hv30=68.1, iv_change_1w=-2.0, price_change_1m=-0.9),
            JPMVolatilityScreen(ticker="VRTX", screen_type="iv_bottom_movers", iv30=29.4, iv_percentile=86, hv30=24.1, iv_change_1w=-2.0, price_change_1m=-1.7),
            JPMVolatilityScreen(ticker="TSCO", screen_type="iv_bottom_movers", iv30=27.5, iv_percentile=86, hv30=22.5, iv_change_1w=-1.9, price_change_1m=0.0),
            JPMVolatilityScreen(ticker="NUE", screen_type="iv_bottom_movers", iv30=30.2, iv_percentile=26, hv30=31.3, iv_change_1w=-1.9, price_change_1m=2.4),
            JPMVolatilityScreen(ticker="M", screen_type="iv_bottom_movers", iv30=46.0, iv_percentile=12, hv30=40.5, iv_change_1w=-1.8, price_change_1m=2.9),
            JPMVolatilityScreen(ticker="LVS", screen_type="iv_bottom_movers", iv30=34.9, iv_percentile=15, hv30=38.0, iv_change_1w=-1.7, price_change_1m=-0.7),
            JPMVolatilityScreen(ticker="TTD", screen_type="iv_bottom_movers", iv30=62.9, iv_percentile=98, hv30=39.9, iv_change_1w=-1.7, price_change_1m=-1.8),
        ]

        # Full stock data (comprehensive from all pages)
        self._all_stocks = self._generate_stock_data()

    def _generate_stock_data(self) -> list[JPMStockData]:
        """Generate comprehensive stock data based on JPM report pages 7-15."""
        # Complete stock landscape data from the report
        stocks_data = [
            # Consumer Discretionary
            {"ticker": "AMZN", "price": 226.5, "iv30": 32.2, "iv_percentile": 30, "hv30": 28.8, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 34.7},
            {"ticker": "TSLA", "price": 438.1, "iv30": 48.3, "iv_percentile": 28, "hv30": 51.1, "sector": "Discretionary", "jpm_rating": "UW", "price_upside": -65.8},
            {"ticker": "HD", "price": 345.8, "iv30": 24.8, "iv_percentile": 66, "hv30": 20.5, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 22.3},
            {"ticker": "MCD", "price": 303.3, "iv30": 18.6, "iv_percentile": 60, "hv30": 15.5, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 0.6},
            {"ticker": "BKNG", "price": 5323.2, "iv30": 27.4, "iv_percentile": 30, "hv30": 23.0, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 17.4},
            {"ticker": "TJX", "price": 154.3, "iv30": 20.4, "iv_percentile": 96, "hv30": 15.4, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": -0.2},
            {"ticker": "LOW", "price": 246.9, "iv30": 25.2, "iv_percentile": 76, "hv30": 21.0, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 21.5},
            {"ticker": "SBUX", "price": 84.0, "iv30": 32.8, "iv_percentile": 65, "hv30": 28.0, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 13.1},
            {"ticker": "NKE", "price": 63.3, "iv30": 34.5, "iv_percentile": 16, "hv30": 38.0, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 35.9},
            {"ticker": "ABNB", "price": 133.0, "iv30": 33.1, "iv_percentile": 98, "hv30": 25.0, "sector": "Discretionary", "jpm_rating": "N", "price_upside": -2.3},
            {"ticker": "GM", "price": 81.0, "iv30": 33.1, "iv_percentile": 26, "hv30": 37.1, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 5.0},
            {"ticker": "TGT", "price": 100.5, "iv30": 38.4, "iv_percentile": 96, "hv30": 31.0, "sector": "Discretionary", "jpm_rating": "N", "price_upside": -0.5},
            {"ticker": "CMG", "price": 37.5, "iv30": 40.4, "iv_percentile": 7, "hv30": 53.4, "sector": "Discretionary", "jpm_rating": "N", "price_upside": 6.7},
            {"ticker": "ULTA", "price": 620.0, "iv30": 33.6, "iv_percentile": 13, "hv30": 38.5, "sector": "Discretionary", "jpm_rating": "OW", "price_upside": 4.3},
            {"ticker": "AAP", "price": 38.9, "iv30": 66.7, "iv_percentile": 91, "hv30": 53.6, "sector": "Discretionary", "jpm_rating": "N", "price_upside": 59.4},
            # Energy
            {"ticker": "XOM", "price": 122.7, "iv30": 21.1, "iv_percentile": 52, "hv30": 17.5, "sector": "Energy", "jpm_rating": "OW", "price_upside": 1.1},
            {"ticker": "CVX", "price": 155.9, "iv30": 23.0, "iv_percentile": 64, "hv30": 20.9, "sector": "Energy", "jpm_rating": "-", "price_upside": 11.6},
            {"ticker": "COP", "price": 96.7, "iv30": 27.4, "iv_percentile": 16, "hv30": 29.6, "sector": "Energy", "jpm_rating": "OW", "price_upside": 5.5},
            {"ticker": "SLB", "price": 40.2, "iv30": 33.8, "iv_percentile": 32, "hv30": 35.5, "sector": "Energy", "jpm_rating": "OW", "price_upside": 7.0},
            {"ticker": "HAL", "price": 29.6, "iv30": 36.9, "iv_percentile": 12, "hv30": 42.1, "sector": "Energy", "jpm_rating": "OW", "price_upside": 1.4},
            {"ticker": "LNG", "price": 197.8, "iv30": 28.5, "iv_percentile": 100, "hv30": 17.1, "sector": "Energy", "jpm_rating": "OW", "price_upside": 44.6},
            {"ticker": "PSX", "price": 130.6, "iv30": 28.6, "iv_percentile": 26, "hv30": 25.0, "sector": "Energy", "jpm_rating": "OW", "price_upside": 17.9},
            # Financials
            {"ticker": "BAC", "price": 56.0, "iv30": 24.5, "iv_percentile": 87, "hv30": 21.4, "sector": "Financials", "jpm_rating": "OW", "price_upside": 9.0},
            {"ticker": "MS", "price": 181.9, "iv30": 28.3, "iv_percentile": 87, "hv30": 24.7, "sector": "Financials", "jpm_rating": "N", "price_upside": -13.7},
            {"ticker": "AXP", "price": 372.7, "iv30": 26.8, "iv_percentile": 43, "hv30": 25.5, "sector": "Financials", "jpm_rating": "N", "price_upside": -3.4},
            {"ticker": "C", "price": 118.7, "iv30": 30.3, "iv_percentile": 89, "hv30": 25.5, "sector": "Financials", "jpm_rating": "OW", "price_upside": 9.5},
            {"ticker": "BX", "price": 158.8, "iv30": 30.6, "iv_percentile": 50, "hv30": 28.0, "sector": "Financials", "jpm_rating": "N", "price_upside": 10.8},
            {"ticker": "COIN", "price": 236.5, "iv30": 58.4, "iv_percentile": 22, "hv30": 63.8, "sector": "Financials", "jpm_rating": "OW", "price_upside": 68.7},
            {"ticker": "PGR", "price": 212.1, "iv30": 26.2, "iv_percentile": 36, "hv30": 24.5, "sector": "Financials", "jpm_rating": "OW", "price_upside": 42.8},
            {"ticker": "ALL", "price": 203.8, "iv30": 21.6, "iv_percentile": 27, "hv30": 18.0, "sector": "Financials", "jpm_rating": "OW", "price_upside": 27.6},
            {"ticker": "AGNC", "price": 10.9, "iv30": 19.1, "iv_percentile": 77, "hv30": 15.2, "sector": "Financials", "jpm_rating": "OW", "price_upside": -8.5},
            # Healthcare
            {"ticker": "LLY", "price": 1080.4, "iv30": 34.8, "iv_percentile": 71, "hv30": 32.0, "sector": "Healthcare", "jpm_rating": "OW", "price_upside": 6.4},
            {"ticker": "JNJ", "price": 207.4, "iv30": 20.2, "iv_percentile": 93, "hv30": 15.8, "sector": "Healthcare", "jpm_rating": "N", "price_upside": -1.1},
            {"ticker": "ABBV", "price": 229.3, "iv30": 26.6, "iv_percentile": 38, "hv30": 24.0, "sector": "Healthcare", "jpm_rating": "OW", "price_upside": 13.4},
            {"ticker": "UNH", "price": 336.4, "iv30": 34.9, "iv_percentile": 77, "hv30": 30.0, "sector": "Healthcare", "jpm_rating": "OW", "price_upside": 26.3},
            {"ticker": "MRK", "price": 106.5, "iv30": 27.1, "iv_percentile": 11, "hv30": 27.0, "sector": "Healthcare", "jpm_rating": "OW", "price_upside": 12.7},
            {"ticker": "PFE", "price": 25.2, "iv30": 22.7, "iv_percentile": 4, "hv30": 22.4, "sector": "Healthcare", "jpm_rating": "N", "price_upside": 19.1},
            {"ticker": "CNC", "price": 41.8, "iv30": 45.8, "iv_percentile": 11, "hv30": 50.0, "sector": "Healthcare", "jpm_rating": "N", "price_upside": -9.0},
            {"ticker": "CI", "price": 279.1, "iv30": 31.5, "iv_percentile": 1, "hv30": 49.3, "sector": "Healthcare", "jpm_rating": "OW", "price_upside": 34.4},
            {"ticker": "MRNA", "price": 30.9, "iv30": 66.7, "iv_percentile": 43, "hv30": 68.1, "sector": "Healthcare", "jpm_rating": "-", "price_upside": -9.3},
            # Industrials
            {"ticker": "GE", "price": 320.8, "iv30": 30.7, "iv_percentile": 82, "hv30": 22.5, "sector": "Industrials", "jpm_rating": "OW", "price_upside": 1.3},
            {"ticker": "CAT", "price": 598.4, "iv30": 35.5, "iv_percentile": 34, "hv30": 32.0, "sector": "Industrials", "jpm_rating": "OW", "price_upside": 22.0},
            {"ticker": "RTX", "price": 187.3, "iv30": 25.7, "iv_percentile": 45, "hv30": 22.5, "sector": "Industrials", "jpm_rating": "OW", "price_upside": 6.8},
            {"ticker": "UBER", "price": 82.9, "iv30": 37.2, "iv_percentile": 57, "hv30": 32.0, "sector": "Industrials", "jpm_rating": "OW", "price_upside": 32.8},
            {"ticker": "UNP", "price": 231.9, "iv30": 21.2, "iv_percentile": 94, "hv30": 16.4, "sector": "Industrials", "jpm_rating": "N", "price_upside": 15.1},
            {"ticker": "HON", "price": 195.9, "iv30": 23.0, "iv_percentile": 51, "hv30": 20.5, "sector": "Industrials", "jpm_rating": "N", "price_upside": 4.9},
            {"ticker": "DE", "price": 466.8, "iv30": 26.5, "iv_percentile": 85, "hv30": 22.7, "sector": "Industrials", "jpm_rating": "N", "price_upside": -1.5},
            {"ticker": "FDX", "price": 293.1, "iv30": 28.5, "iv_percentile": 85, "hv30": 22.0, "sector": "Industrials", "jpm_rating": "N", "price_upside": 0.3},
            {"ticker": "NSC", "price": 287.8, "iv30": 21.8, "iv_percentile": 99, "hv30": 13.7, "sector": "Industrials", "jpm_rating": "N", "price_upside": 5.3},
            # Technology
            {"ticker": "NVDA", "price": 188.9, "iv30": 43.7, "iv_percentile": 82, "hv30": 38.0, "sector": "Technology", "jpm_rating": "OW", "price_upside": 32.4},
            {"ticker": "AAPL", "price": 271.0, "iv30": 23.3, "iv_percentile": 60, "hv30": 20.5, "sector": "Technology", "jpm_rating": "OW", "price_upside": 12.5},
            {"ticker": "MSFT", "price": 472.9, "iv30": 25.2, "iv_percentile": 96, "hv30": 19.8, "sector": "Technology", "jpm_rating": "OW", "price_upside": 21.6},
            {"ticker": "AVGO", "price": 347.6, "iv30": 48.5, "iv_percentile": 14, "hv30": 54.3, "sector": "Technology", "jpm_rating": "OW", "price_upside": 36.6},
            {"ticker": "ORCL", "price": 195.7, "iv30": 51.3, "iv_percentile": 1, "hv30": 52.9, "sector": "Technology", "jpm_rating": "N", "price_upside": 17.5},
            {"ticker": "AMD", "price": 223.5, "iv30": 53.2, "iv_percentile": 4, "hv30": 58.0, "sector": "Technology", "jpm_rating": "N", "price_upside": 20.8},
            {"ticker": "CRM", "price": 253.6, "iv30": 34.7, "iv_percentile": 41, "hv30": 32.0, "sector": "Technology", "jpm_rating": "OW", "price_upside": 43.9},
            {"ticker": "INTC", "price": 39.4, "iv30": 53.9, "iv_percentile": 6, "hv30": 52.9, "sector": "Technology", "jpm_rating": "UW", "price_upside": -23.8},
            {"ticker": "NOW", "price": 147.5, "iv30": 36.6, "iv_percentile": 54, "hv30": 32.0, "sector": "Technology", "jpm_rating": "OW", "price_upside": 45.8},
            {"ticker": "DDOG", "price": 133.8, "iv30": 46.6, "iv_percentile": 6, "hv30": 57.0, "sector": "Technology", "jpm_rating": "OW", "price_upside": 49.5},
            {"ticker": "DOCU", "price": 64.9, "iv30": 42.0, "iv_percentile": 22, "hv30": 37.6, "sector": "Technology", "jpm_rating": "N", "price_upside": 20.3},
            {"ticker": "SNOW", "price": 216.7, "iv30": 46.0, "iv_percentile": 8, "hv30": 42.3, "sector": "Technology", "jpm_rating": "OW", "price_upside": 23.7},
            {"ticker": "INTU", "price": 629.5, "iv30": 31.0, "iv_percentile": 89, "hv30": 26.1, "sector": "Technology", "jpm_rating": "OW", "price_upside": 19.1},
            {"ticker": "ADBE", "price": 333.3, "iv30": 34.4, "iv_percentile": 84, "hv30": 30.0, "sector": "Technology", "jpm_rating": "OW", "price_upside": 56.0},
            {"ticker": "PANW", "price": 179.4, "iv30": 35.1, "iv_percentile": 91, "hv30": 28.9, "sector": "Technology", "jpm_rating": "OW", "price_upside": 31.0},
            {"ticker": "CRWD", "price": 453.6, "iv30": 40.7, "iv_percentile": 39, "hv30": 35.0, "sector": "Technology", "jpm_rating": "OW", "price_upside": 28.3},
            {"ticker": "PSTG", "price": 69.0, "iv30": 54.5, "iv_percentile": 1, "hv30": 82.1, "sector": "Technology", "jpm_rating": "OW", "price_upside": 52.2},
            {"ticker": "MU", "price": 315.4, "iv30": 65.6, "iv_percentile": 31, "hv30": 69.4, "sector": "Technology", "jpm_rating": "OW", "price_upside": 11.0},
            {"ticker": "FTNT", "price": 77.9, "iv30": 37.5, "iv_percentile": 97, "hv30": 28.3, "sector": "Technology", "jpm_rating": "UW", "price_upside": -3.7},
            {"ticker": "OKTA", "price": 83.6, "iv30": 43.6, "iv_percentile": 97, "hv30": 31.1, "sector": "Technology", "jpm_rating": "OW", "price_upside": 44.7},
            # Consumer Staples
            {"ticker": "WMT", "price": 112.8, "iv30": 25.3, "iv_percentile": 75, "hv30": 22.0, "sector": "Staples", "jpm_rating": "OW", "price_upside": 14.4},
            {"ticker": "COST", "price": 854.5, "iv30": 22.8, "iv_percentile": 87, "hv30": 18.3, "sector": "Staples", "jpm_rating": "OW", "price_upside": 20.2},
            {"ticker": "PG", "price": 141.8, "iv30": 20.0, "iv_percentile": 79, "hv30": 17.5, "sector": "Staples", "jpm_rating": "N", "price_upside": 10.7},
            {"ticker": "KO", "price": 69.1, "iv30": 17.1, "iv_percentile": 46, "hv30": 15.0, "sector": "Staples", "jpm_rating": "OW", "price_upside": 14.3},
            {"ticker": "PEP", "price": 142.2, "iv30": 20.0, "iv_percentile": 30, "hv30": 17.5, "sector": "Staples", "jpm_rating": "OW", "price_upside": 15.3},
            {"ticker": "PM", "price": 160.3, "iv30": 26.5, "iv_percentile": 58, "hv30": 23.0, "sector": "Staples", "jpm_rating": "OW", "price_upside": 15.4},
            {"ticker": "CPB", "price": 27.7, "iv30": 27.3, "iv_percentile": 10, "hv30": 25.6, "sector": "Staples", "jpm_rating": "N", "price_upside": 11.9},
            {"ticker": "CLX", "price": 100.9, "iv30": 30.7, "iv_percentile": 92, "hv30": 23.5, "sector": "Staples", "jpm_rating": "N", "price_upside": 19.0},
            {"ticker": "DG", "price": 136.8, "iv30": 34.3, "iv_percentile": 7, "hv30": 43.0, "sector": "Staples", "jpm_rating": "OW", "price_upside": 21.3},
            # Materials
            {"ticker": "LIN", "price": 429.1, "iv30": 21.3, "iv_percentile": 85, "hv30": 17.5, "sector": "Materials", "jpm_rating": "OW", "price_upside": 6.0},
            {"ticker": "FCX", "price": 51.9, "iv30": 39.8, "iv_percentile": 2, "hv30": 37.0, "sector": "Materials", "jpm_rating": "OW", "price_upside": 11.7},
            {"ticker": "NEM", "price": 101.2, "iv30": 44.7, "iv_percentile": 21, "hv30": 50.0, "sector": "Materials", "jpm_rating": "-", "price_upside": 11.1},
            {"ticker": "SHW", "price": 327.8, "iv30": 24.8, "iv_percentile": 68, "hv30": 21.0, "sector": "Materials", "jpm_rating": "OW", "price_upside": 17.4},
            {"ticker": "SCCO", "price": 148.7, "iv30": 38.2, "iv_percentile": 21, "hv30": 42.0, "sector": "Materials", "jpm_rating": "N", "price_upside": -19.6},
            {"ticker": "AA", "price": 56.5, "iv30": 53.8, "iv_percentile": 24, "hv30": 58.0, "sector": "Materials", "jpm_rating": "N", "price_upside": -20.4},
            # Communication Services
            {"ticker": "GOOGL", "price": 315.2, "iv30": 33.1, "iv_percentile": 42, "hv30": 29.0, "sector": "Communication", "jpm_rating": "OW", "price_upside": 22.2},
            {"ticker": "META", "price": 650.4, "iv30": 33.2, "iv_percentile": 42, "hv30": 29.0, "sector": "Communication", "jpm_rating": "OW", "price_upside": 23.0},
            {"ticker": "NFLX", "price": 1085.1, "iv30": 25.1, "iv_percentile": 61, "hv30": 22.0, "sector": "Communication", "jpm_rating": "N", "price_upside": 14.6},
            {"ticker": "DIS", "price": 111.9, "iv30": 27.4, "iv_percentile": 79, "hv30": 23.5, "sector": "Communication", "jpm_rating": "OW", "price_upside": 23.4},
            {"ticker": "VZ", "price": 40.5, "iv30": 19.5, "iv_percentile": 20, "hv30": 20.1, "sector": "Communication", "jpm_rating": "N", "price_upside": 16.0},
            {"ticker": "T", "price": 24.6, "iv30": 23.0, "iv_percentile": 76, "hv30": 20.0, "sector": "Communication", "jpm_rating": "OW", "price_upside": 34.4},
            {"ticker": "SPOT", "price": 575.0, "iv30": 41.1, "iv_percentile": 99, "hv30": 29.5, "sector": "Communication", "jpm_rating": "OW", "price_upside": 40.0},
            {"ticker": "TTD", "price": 37.7, "iv30": 62.9, "iv_percentile": 98, "hv30": 39.9, "sector": "Communication", "jpm_rating": "-", "price_upside": 59.2},
            {"ticker": "RBLX", "price": 81.0, "iv30": 57.9, "iv_percentile": 74, "hv30": 51.5, "sector": "Communication", "jpm_rating": "N", "price_upside": 23.5},
            # Real Estate
            {"ticker": "PLD", "price": 129.1, "iv30": 23.3, "iv_percentile": 65, "hv30": 20.0, "sector": "Real Estate", "jpm_rating": "OW", "price_upside": 4.6},
            {"ticker": "AMT", "price": 174.8, "iv30": 22.9, "iv_percentile": 72, "hv30": 20.0, "sector": "Real Estate", "jpm_rating": "OW", "price_upside": 43.0},
            {"ticker": "EQIX", "price": 764.1, "iv30": 25.8, "iv_percentile": 86, "hv30": 22.0, "sector": "Real Estate", "jpm_rating": "OW", "price_upside": 24.3},
            {"ticker": "SPG", "price": 184.0, "iv30": 20.5, "iv_percentile": 87, "hv30": 15.5, "sector": "Real Estate", "jpm_rating": "N", "price_upside": 7.6},
            # Utilities
            {"ticker": "NEE", "price": 80.9, "iv30": 24.3, "iv_percentile": 70, "hv30": 19.0, "sector": "Utilities", "jpm_rating": "OW", "price_upside": 19.9},
            {"ticker": "SO", "price": 87.2, "iv30": 17.8, "iv_percentile": 83, "hv30": 15.9, "sector": "Utilities", "jpm_rating": "N", "price_upside": 6.7},
            {"ticker": "DUK", "price": 117.4, "iv30": 15.5, "iv_percentile": 57, "hv30": 14.6, "sector": "Utilities", "jpm_rating": "N", "price_upside": 7.3},
            # High volatility / Meme / Crypto
            {"ticker": "GME", "price": 78.5, "iv30": 78.5, "iv_percentile": 88, "hv30": 65.2, "sector": "Discretionary", "jpm_rating": "-", "price_upside": 0.0},
            {"ticker": "PLUG", "price": 2.2, "iv30": 101.7, "iv_percentile": 9, "hv30": 88.3, "sector": "Industrials", "jpm_rating": "N", "price_upside": 12.1},
            {"ticker": "WOLF", "price": 18.9, "iv30": 109.5, "iv_percentile": 24, "hv30": 87.7, "sector": "Technology", "jpm_rating": "UW", "price_upside": 58.5},
            {"ticker": "LCID", "price": 11.2, "iv30": 90.2, "iv_percentile": 95, "hv30": 63.4, "sector": "Discretionary", "jpm_rating": "-", "price_upside": 48.0},
            {"ticker": "RIVN", "price": 19.4, "iv30": 70.1, "iv_percentile": 23, "hv30": 60.0, "sector": "Discretionary", "jpm_rating": "UW", "price_upside": -48.5},
            {"ticker": "PTON", "price": 6.1, "iv30": 64.9, "iv_percentile": 70, "hv30": 52.8, "sector": "Discretionary", "jpm_rating": "N", "price_upside": 47.1},
            {"ticker": "BILL", "price": 50.6, "iv30": 57.8, "iv_percentile": 55, "hv30": 43.8, "sector": "Technology", "jpm_rating": "OW", "price_upside": 18.7},
            {"ticker": "QS", "price": 11.1, "iv30": 85.5, "iv_percentile": 4, "hv30": 96.2, "sector": "Discretionary", "jpm_rating": "-", "price_upside": 8.5},
            {"ticker": "SMCI", "price": 85.2, "iv30": 85.2, "iv_percentile": 95, "hv30": 72.5, "sector": "Technology", "jpm_rating": "-", "price_upside": 0.0},
        ]

        result = []
        for s in stocks_data:
            iv30 = s["iv30"]
            hv30 = s.get("hv30", iv30 * 0.9)
            result.append(
                JPMStockData(
                    ticker=s["ticker"],
                    price=s.get("price"),
                    iv30=iv30,
                    iv60=iv30 * 1.02,
                    iv90=iv30 * 1.05,
                    iv_percentile=s["iv_percentile"],
                    iv_rank=s["iv_percentile"] * 0.95,
                    hv30=hv30,
                    hv60=hv30 * 1.02,
                    iv_hv_spread=round(iv30 - hv30, 2),
                    skew=round((s["iv_percentile"] - 50) / 20, 2),
                    term_structure="contango" if iv30 < iv30 * 1.05 else "backwardation",
                    sector=s.get("sector"),
                )
            )
        return result

    def get_metadata(self) -> JPMReportMetadata:
        """Get report metadata."""
        return JPMReportMetadata(
            report_date=self._report_date,
            report_title="US Single Stock Volatility Chartbook",
            source="J.P. Morgan Global Equity Derivatives Strategy",
            total_stocks=len(self._all_stocks),
            last_updated=datetime.now(),
        )

    def get_trading_candidates(
        self, strategy: JPMStrategyType | None = None
    ) -> list[JPMTradingCandidate]:
        """Get trading candidates, optionally filtered by strategy."""
        if strategy == "call_overwriting":
            return self._call_overwriting
        elif strategy == "call_buying":
            return self._call_buying
        elif strategy == "put_underwriting":
            return self._put_underwriting
        elif strategy == "put_buying":
            return self._put_buying
        else:
            # Return all
            return (
                self._call_overwriting
                + self._call_buying
                + self._put_underwriting
                + self._put_buying
            )

    def get_volatility_screen(
        self, screen_type: JPMScreenType | None = None
    ) -> list[JPMVolatilityScreen]:
        """Get volatility screen results."""
        if screen_type == "rich_iv":
            return self._rich_iv
        elif screen_type == "cheap_iv":
            return self._cheap_iv
        elif screen_type == "iv_top_movers":
            return self._iv_top_movers
        elif screen_type == "iv_bottom_movers":
            return self._iv_bottom_movers
        else:
            # Return all screens
            return (
                self._rich_iv
                + self._cheap_iv
                + self._iv_top_movers
                + self._iv_bottom_movers
            )

    def get_all_stocks(
        self,
        sort_by: str = "ticker",
        ascending: bool = True,
        sector: str | None = None,
        iv_percentile_min: float | None = None,
        iv_percentile_max: float | None = None,
    ) -> list[JPMStockData]:
        """Get all stock data with optional filtering and sorting."""
        result = self._all_stocks.copy()

        # Apply filters
        if sector:
            result = [s for s in result if s.sector and sector.lower() in s.sector.lower()]
        if iv_percentile_min is not None:
            result = [s for s in result if s.iv_percentile >= iv_percentile_min]
        if iv_percentile_max is not None:
            result = [s for s in result if s.iv_percentile <= iv_percentile_max]

        # Apply sorting
        reverse = not ascending
        if sort_by == "ticker":
            result.sort(key=lambda x: x.ticker, reverse=reverse)
        elif sort_by == "iv30":
            result.sort(key=lambda x: x.iv30, reverse=reverse)
        elif sort_by == "iv_percentile":
            result.sort(key=lambda x: x.iv_percentile, reverse=reverse)
        elif sort_by == "iv_hv_spread":
            result.sort(key=lambda x: x.iv_hv_spread or 0, reverse=reverse)

        return result

    def get_stock(self, ticker: str) -> JPMStockData | None:
        """Get single stock data by ticker."""
        ticker_upper = ticker.upper()
        for stock in self._all_stocks:
            if stock.ticker == ticker_upper:
                return stock
        return None

    def get_candidates_for_symbol(self, ticker: str) -> list[JPMTradingCandidate]:
        """Get all trading candidates for a specific symbol."""
        ticker_upper = ticker.upper()
        all_candidates = self.get_trading_candidates()
        return [c for c in all_candidates if c.ticker == ticker_upper]

    def get_full_research_data(self) -> JPMResearchData:
        """Get complete research data."""
        return JPMResearchData(
            metadata=self.get_metadata(),
            call_overwriting=self._call_overwriting,
            call_buying=self._call_buying,
            put_underwriting=self._put_underwriting,
            put_buying=self._put_buying,
            rich_iv=self._rich_iv,
            cheap_iv=self._cheap_iv,
            iv_top_movers=self._iv_top_movers,
            iv_bottom_movers=self._iv_bottom_movers,
            all_stocks=self._all_stocks,
        )

    def get_summary(self) -> dict:
        """Get a summary of the research data."""
        return {
            "report_date": str(self._report_date),
            "total_stocks": len(self._all_stocks),
            "call_overwriting_candidates": len(self._call_overwriting),
            "call_buying_candidates": len(self._call_buying),
            "put_underwriting_candidates": len(self._put_underwriting),
            "put_buying_candidates": len(self._put_buying),
            "rich_iv_stocks": len(self._rich_iv),
            "cheap_iv_stocks": len(self._cheap_iv),
            "top_call_overwriting": [c.ticker for c in self._call_overwriting[:3]],
            "top_call_buying": [c.ticker for c in self._call_buying[:3]],
            "top_put_underwriting": [c.ticker for c in self._put_underwriting[:3]],
            "top_put_buying": [c.ticker for c in self._put_buying[:3]],
        }


# Singleton instance
jpm_research_service = JPMResearchService()
