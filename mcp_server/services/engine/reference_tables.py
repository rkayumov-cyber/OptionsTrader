"""Quantitative reference tables (Section 9).

Backtested performance data from Goldman Sachs and JPMorgan research.
"""

from mcp_server.engine_models import (
    GlobalVolLevel,
    HedgingComparison,
    OverwritingPerformance,
    PutSellingPerformance,
    SectorEventSensitivity,
    TailTradingPerformance,
    VolRiskPremium,
    ZeroDTEVolPremium,
)


class ReferenceTables:
    """Access to all 8 backtested performance reference tables."""

    # 9.1 Put Selling Performance by Delta (GS 10-Year Study)
    PUT_SELLING: list[PutSellingPerformance] = [
        PutSellingPerformance(
            delta=70, ann_return=7.1, sharpe=0.50, std_dev=17.0,
            win_rate=0.68, avg_premium=0.24,
        ),
        PutSellingPerformance(
            delta=60, ann_return=6.9, sharpe=0.51, std_dev=16.0,
            win_rate=0.56, avg_premium=0.19,
        ),
        PutSellingPerformance(
            delta=50, ann_return=6.3, sharpe=0.50, std_dev=14.5,
            win_rate=0.44, avg_premium=0.14,
        ),
        PutSellingPerformance(
            delta=40, ann_return=5.6, sharpe=0.50, std_dev=12.6,
            win_rate=0.32, avg_premium=0.10,
        ),
        PutSellingPerformance(
            delta=30, ann_return=4.8, sharpe=0.50, std_dev=10.1,
            win_rate=0.23, avg_premium=0.07,
        ),
        PutSellingPerformance(
            delta=20, ann_return=3.8, sharpe=0.54, std_dev=7.6,
            win_rate=0.15, avg_premium=0.04,
        ),
    ]

    # 9.2 Overwriting Performance by FCF Yield Quintile (GS 16-Year Study)
    OVERWRITING: list[OverwritingPerformance] = [
        OverwritingPerformance(
            fcf_quintile="Q1 (Low)", ann_return=2.6, sharpe=0.27, std_dev=13.0,
        ),
        OverwritingPerformance(
            fcf_quintile="Q2", ann_return=6.1, sharpe=0.62, std_dev=11.0,
        ),
        OverwritingPerformance(
            fcf_quintile="Q3", ann_return=7.9, sharpe=0.92, std_dev=9.0,
        ),
        OverwritingPerformance(
            fcf_quintile="Q4", ann_return=7.9, sharpe=0.91, std_dev=9.0,
        ),
        OverwritingPerformance(
            fcf_quintile="Q5 (High)", ann_return=8.8, sharpe=0.90, std_dev=10.0,
        ),
    ]

    # 9.3 Hedging Strategy Comparison (GS 27-Year Backtest)
    HEDGING: list[HedgingComparison] = [
        HedgingComparison(
            strategy="S&P 500 (unhedged)",
            ann_return=9.2, vol=18.2, sharpe=0.51, max_dd=-38.0,
        ),
        HedgingComparison(
            strategy="Put Spread Collar 3m/3m",
            ann_return=7.6, vol=8.8, sharpe=0.88, max_dd=-14.0,
        ),
        HedgingComparison(
            strategy="Long Put (monthly roll)",
            ann_return=6.0, vol=10.8, sharpe=0.56, max_dd=-13.0,
        ),
        HedgingComparison(
            strategy="Put Spread",
            ann_return=7.5, vol=13.5, sharpe=0.56, max_dd=-17.0,
        ),
        HedgingComparison(
            strategy="Covered Call (10% OTM)",
            ann_return=10.7, vol=14.0, sharpe=0.76, max_dd=-25.0,
        ),
        HedgingComparison(
            strategy="Put Selling (10% OTM)",
            ann_return=5.5, vol=7.0, sharpe=0.76, max_dd=-22.0,
        ),
    ]

    # 9.4 Macro Event Sensitivity by Sector (GS 15-Year Study)
    SECTOR_SENSITIVITY: list[SectorEventSensitivity] = [
        SectorEventSensitivity(
            sector="Energy",
            activity=0.1, credit=0.2, employment=0.1,
            housing=0.1, oil=0.8, policy=0.1, prices=0.4,
        ),
        SectorEventSensitivity(
            sector="Real Estate",
            activity=0.1, credit=0.4, employment=0.3,
            housing=0.8, oil=0.1, policy=0.3, prices=0.1,
        ),
        SectorEventSensitivity(
            sector="Financials",
            activity=0.1, credit=0.5, employment=0.1,
            housing=0.4, oil=0.1, policy=0.4, prices=0.3,
        ),
        SectorEventSensitivity(
            sector="Tech",
            activity=0.1, credit=0.1, employment=0.2,
            housing=0.1, oil=0.1, policy=0.2, prices=0.2,
        ),
        SectorEventSensitivity(
            sector="Healthcare",
            activity=0.1, credit=0.1, employment=0.1,
            housing=0.1, oil=0.1, policy=0.2, prices=0.1,
        ),
    ]

    # 9.5 Global Vol Levels & Percentiles (JPM, Aug 2025)
    GLOBAL_VOL: list[GlobalVolLevel] = [
        GlobalVolLevel(
            index="SPX", iv_1m=21.2, pctile_1m_5y=15.5,
            iv_3m=22.5, pctile_3m_5y=18.2, variance_basis_1m=-3.3,
        ),
        GlobalVolLevel(
            index="NDX", iv_1m=19.0, pctile_1m_5y=12.5,
            iv_3m=21.0, pctile_3m_5y=10.5, variance_basis_1m=7.7,
        ),
        GlobalVolLevel(
            index="DAX", iv_1m=15.2, pctile_1m_5y=23.4,
            iv_3m=15.9, pctile_3m_5y=24.1, variance_basis_1m=-6.3,
        ),
        GlobalVolLevel(
            index="HSCEI", iv_1m=22.1, pctile_1m_5y=15.2,
            iv_3m=22.4, pctile_3m_5y=24.3, variance_basis_1m=0.0,
        ),
    ]

    # 9.6 0DTE Day-of-Week Vol Premium (JPM)
    ZERO_DTE_PREMIUM: list[ZeroDTEVolPremium] = [
        ZeroDTEVolPremium(
            day="Monday", ndx_premium="3.2-4.5%",
            gamma_imbalance="-175 to -125bps", bias="SELL",
        ),
        ZeroDTEVolPremium(
            day="Tuesday", ndx_premium="3.2-4.5%",
            gamma_imbalance="-125 to -100bps", bias="SELL",
        ),
        ZeroDTEVolPremium(
            day="Wednesday", ndx_premium="2.2-2.5%",
            gamma_imbalance="-50bps", bias="AVOID/BUY",
        ),
        ZeroDTEVolPremium(
            day="Thursday", ndx_premium="2.2-2.5%",
            gamma_imbalance="-75bps", bias="SELECTIVE",
        ),
        ZeroDTEVolPremium(
            day="Friday", ndx_premium="3.0-3.5%",
            gamma_imbalance="-150bps", bias="SELL",
        ),
    ]

    # 9.7 Vol Risk Premium Matrix (JPM Systematic Vol)
    VOL_RISK_PREMIUM: list[VolRiskPremium] = [
        VolRiskPremium(tenor="2Y", atm=42, otm_25d=25, otm_10d=12, otm_5d=3),
        VolRiskPremium(tenor="5Y", atm=16, otm_25d=10, otm_10d=5, otm_5d=3),
        VolRiskPremium(tenor="10Y", atm=7, otm_25d=3, otm_10d=-1, otm_5d=-3),
        VolRiskPremium(tenor="20Y", atm=2, otm_25d=-3, otm_10d=-8, otm_5d=-12),
    ]

    # 9.8 Three-Pillar Tail Trading Performance (JPM)
    TAIL_TRADING: list[TailTradingPerformance] = [
        TailTradingPerformance(
            configuration="SPX only",
            ann_return=12.5, vol=18.2, sharpe=0.69, max_dd=-31.0,
        ),
        TailTradingPerformance(
            configuration="SPX + Put Spread",
            ann_return=10.2, vol=14.8, sharpe=0.69, max_dd=-12.0,
        ),
        TailTradingPerformance(
            configuration="SPX + Tail + Put Spread",
            ann_return=17.1, vol=15.4, sharpe=1.11, max_dd=-17.6,
        ),
        TailTradingPerformance(
            configuration="2025 YTD: PS only",
            ann_return=0.8, vol=None, sharpe=None, max_dd=None,
        ),
        TailTradingPerformance(
            configuration="2025 YTD: PS + Tail",
            ann_return=7.6, vol=None, sharpe=None, max_dd=None,
        ),
    ]

    TABLES = {
        "put_selling": "PUT_SELLING",
        "overwriting": "OVERWRITING",
        "hedging": "HEDGING",
        "sector_sensitivity": "SECTOR_SENSITIVITY",
        "global_vol": "GLOBAL_VOL",
        "zero_dte_premium": "ZERO_DTE_PREMIUM",
        "vol_risk_premium": "VOL_RISK_PREMIUM",
        "tail_trading": "TAIL_TRADING",
    }

    @classmethod
    def get_table(cls, name: str) -> list:
        """Retrieve a reference table by name."""
        attr = cls.TABLES.get(name)
        if attr is None:
            raise ValueError(
                f"Unknown table '{name}'. Available: {list(cls.TABLES.keys())}"
            )
        return getattr(cls, attr)

    @classmethod
    def list_tables(cls) -> list[str]:
        """List all available table names."""
        return list(cls.TABLES.keys())
