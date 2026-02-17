"""Event-specific playbooks (Section 7).

FOMC, Earnings, and 0DTE playbooks with timing, strategy, and sizing.
"""

from mcp_server.engine_models import (
    DayOfWeek,
    EventPlaybook,
    EventType,
    PlaybookPhase,
    PlaybookPhaseDetail,
    ZeroDTEDayInfo,
    ZeroDTEPlaybook,
)


class EventPlaybooks:
    """Event playbook provider for FOMC, Earnings, CPI/NFP, and 0DTE."""

    # ── FOMC Playbook (Section 7.1) ───────────────────────────────────

    FOMC = EventPlaybook(
        event_type=EventType.FOMC,
        phases=[
            PlaybookPhaseDetail(
                phase=PlaybookPhase.PRE_EVENT,
                timing="T-5 to T-3",
                iv_behavior="Front-end IV expansion begins [GS Trading Events 15yr]",
                strategy="Buy calendar spreads (sell front-week, buy front+30 DTE)",
                sizing="Standard",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.EVENT_EVE,
                timing="T-1",
                iv_behavior="IV peaks. Premium richest.",
                strategy="Initiate short front-end vol (straddle sell or calendar) if comfortable",
                sizing="50% of standard (gap risk)",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.POST_EVENT,
                timing="T+0 to T+1",
                iv_behavior="30-60% of front-end excess IV evaporates within 24hrs [GS Trading Events]",
                strategy="Close calendars. If directional view, enter cheap debit spreads.",
                sizing="Standard (post-crush, vol cheap)",
            ),
        ],
        notes=[
            "FOMC produces largest implied moves of all macro events [GS 15yr]",
            "Multi-event weeks (FOMC + CPI): IV premium rises ~40% above baseline",
            "Fed rate decisions show most persistent significance [GS Trading Events]",
        ],
    )

    # ── Earnings Playbook (Section 7.2) ───────────────────────────────

    EARNINGS = EventPlaybook(
        event_type=EventType.EARNINGS,
        phases=[
            PlaybookPhaseDetail(
                phase=PlaybookPhase.PRE_EVENT,
                timing="T-5 to T-3",
                iv_behavior="20-40% above normal IV [JPM Earnings & Options]",
                strategy="VIX-conditional: <20 = calendars; 20-35 = iron condors at implied move; "
                         "35-45 = call buying (+37% avg ROP); >45 = short strangles (+8% ROP)",
                sizing="Standard",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.EVENT_EVE,
                timing="T-1",
                iv_behavior="Peak IV expansion",
                strategy="Position per VIX-conditional matrix above; no adjustments day-of",
                sizing="50% if first earnings play",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.POST_EVENT,
                timing="T+0 to T+1",
                iv_behavior="IV crush of 30-60%",
                strategy="Close all event-specific positions within 24 hours post-report",
                sizing="N/A - closing only",
            ),
        ],
        key_rules=[
            "Avg S&P stock moves +/-4.3% on earnings (18yr avg) [GS Earnings 18yr]",
            "Options market prices +/-5.6% (systematically overestimates) [GS Earnings 18yr]",
            "Sticker shock: stocks >$100 have underpriced earnings moves [GS Earnings 18yr]",
            "Call buying profitable 15/15 years, +13% avg ROP [GS Earnings Vol]",
            "Tech implied moves 1.5-2.0x realized [JPM Earnings & Options]",
            "Financials implied ~1.1-1.2x realized [JPM Earnings & Options]",
        ],
    )

    # ── CPI Playbook ──────────────────────────────────────────────────

    CPI = EventPlaybook(
        event_type=EventType.CPI,
        phases=[
            PlaybookPhaseDetail(
                phase=PlaybookPhase.PRE_EVENT,
                timing="T-3 to T-1",
                iv_behavior="Front-end IV expansion, less than FOMC [GS Trading Events]",
                strategy="Calendar spreads or short front-end straddles",
                sizing="75% of standard",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.EVENT_EVE,
                timing="T-1",
                iv_behavior="IV peaks pre-release",
                strategy="Short front-end vol if IV expansion > 20% above normal",
                sizing="50% of standard",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.POST_EVENT,
                timing="T+0",
                iv_behavior="Quick IV crush, often completes within hours",
                strategy="Close event trades. Directional entries if view formed.",
                sizing="Standard post-event",
            ),
        ],
        notes=[
            "CPI second-most impactful after FOMC [GS Trading Events 15yr]",
            "Multi-event weeks add ~40% IV premium",
        ],
    )

    # ── NFP Playbook ──────────────────────────────────────────────────

    NFP = EventPlaybook(
        event_type=EventType.NFP,
        phases=[
            PlaybookPhaseDetail(
                phase=PlaybookPhase.PRE_EVENT,
                timing="T-3 to T-1",
                iv_behavior="Moderate front-end IV expansion [GS Trading Events]",
                strategy="Calendar spreads if IV premium > 15% above normal",
                sizing="75% of standard",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.EVENT_EVE,
                timing="T-1 (Thursday before)",
                iv_behavior="IV plateaus",
                strategy="Short front-end straddle if premium rich, or wait",
                sizing="50% of standard",
            ),
            PlaybookPhaseDetail(
                phase=PlaybookPhase.POST_EVENT,
                timing="T+0 (Friday)",
                iv_behavior="IV normalizes",
                strategy="Close event positions",
                sizing="Standard post-event",
            ),
        ],
        notes=[
            "NFP less impactful than FOMC/CPI but still material [GS Trading Events]",
            "Often coincides with Friday 0DTE elevated premium",
        ],
    )

    # ── 0DTE Playbook (Section 7.3) ───────────────────────────────────

    ZERO_DTE = ZeroDTEPlaybook(
        characteristics={
            "theta": "100% decays in single day [JPM Same-day Options]",
            "gamma": "Extreme - binary-like instruments",
            "sizing": "0.1-0.25% of NAV per trade (max)",
            "ndx_vol_correlation": 0.88,
            "ndx_market_share": "~60% of Nasdaq 100 option volume [JPM]",
        },
        days=[
            ZeroDTEDayInfo(
                day=DayOfWeek.MONDAY,
                premium="HIGH (3.2-4.5%)",
                bias="SELL straddles at 10am",
                gamma_imbalance="-175 to -125bps",
            ),
            ZeroDTEDayInfo(
                day=DayOfWeek.TUESDAY,
                premium="HIGH",
                bias="SELL straddles at 10am",
                gamma_imbalance="-125 to -100bps",
            ),
            ZeroDTEDayInfo(
                day=DayOfWeek.WEDNESDAY,
                premium="LOW (2.2-2.5%)",
                bias="AVOID or buy premium",
                gamma_imbalance="-50bps",
            ),
            ZeroDTEDayInfo(
                day=DayOfWeek.THURSDAY,
                premium="LOW",
                bias="Selective selling only",
                gamma_imbalance="-75bps",
            ),
            ZeroDTEDayInfo(
                day=DayOfWeek.FRIDAY,
                premium="ELEVATED",
                bias="SELL if no weekend event risk",
                gamma_imbalance="-150bps",
            ),
        ],
        entry_rule="Theta must exceed 2x expected intraday move [JPM P&L Attribution]",
        event_block="No 0DTE on FOMC/CPI/NFP days [JPM Same-day Options]",
    )

    PLAYBOOKS: dict[EventType, EventPlaybook] = {
        EventType.FOMC: FOMC,
        EventType.EARNINGS: EARNINGS,
        EventType.CPI: CPI,
        EventType.NFP: NFP,
    }

    @classmethod
    def get_playbook(cls, event_type: EventType) -> EventPlaybook:
        """Get a playbook by event type."""
        pb = cls.PLAYBOOKS.get(event_type)
        if pb is None:
            raise ValueError(f"No playbook for event type '{event_type}'")
        return pb

    @classmethod
    def get_zero_dte(cls) -> ZeroDTEPlaybook:
        """Get the 0DTE playbook."""
        return cls.ZERO_DTE

    @classmethod
    def get_zero_dte_day(cls, day: DayOfWeek) -> ZeroDTEDayInfo:
        """Get 0DTE recommendation for a specific day."""
        for d in cls.ZERO_DTE.days:
            if d.day == day:
                return d
        raise ValueError(f"No 0DTE data for '{day}'")
