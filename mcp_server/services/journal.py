"""Trade journal service."""

import uuid
from datetime import datetime
from mcp_server.models import TradeEntry, TradeStats, Market
from .storage import storage


class JournalService:
    """Trade journal management."""

    STORAGE_KEY = "journal"

    def __init__(self):
        self._trades: dict[str, TradeEntry] = {}
        self._load()

    def _load(self):
        """Load trades from storage."""
        self._trades = storage.load_dict(self.STORAGE_KEY, TradeEntry)

    def _save(self):
        """Save trades to storage."""
        storage.save_dict(self.STORAGE_KEY, self._trades)

    def get_all(self) -> list[TradeEntry]:
        """Get all trades."""
        trades = list(self._trades.values())
        trades.sort(key=lambda x: x.entry_date, reverse=True)
        return trades

    def get_by_id(self, trade_id: str) -> TradeEntry | None:
        """Get trade by ID."""
        return self._trades.get(trade_id)

    def get_open_trades(self) -> list[TradeEntry]:
        """Get open trades only."""
        return [t for t in self._trades.values() if t.status == "open"]

    def get_closed_trades(self) -> list[TradeEntry]:
        """Get closed trades only."""
        return [t for t in self._trades.values() if t.status == "closed"]

    def create(
        self,
        symbol: str,
        market: Market,
        entry_price: float,
        quantity: int,
        strategy: str = "Custom",
        notes: str = "",
        tags: list[str] | None = None,
    ) -> TradeEntry:
        """Create a new trade entry."""
        trade_id = str(uuid.uuid4())[:8]

        trade = TradeEntry(
            id=trade_id,
            symbol=symbol,
            market=market,
            strategy=strategy,
            entry_date=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            status="open",
            notes=notes,
            tags=tags or [],
        )

        self._trades[trade_id] = trade
        self._save()
        return trade

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        notes: str = "",
        lessons: str = "",
    ) -> TradeEntry | None:
        """Close a trade with exit details."""
        trade = self._trades.get(trade_id)
        if not trade:
            return None

        trade.exit_date = datetime.now()
        trade.exit_price = exit_price
        trade.status = "closed"

        # Calculate P/L
        trade.pnl = (exit_price - trade.entry_price) * trade.quantity
        trade.pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100

        if notes:
            trade.notes = (trade.notes + "\n\n" + notes).strip()
        if lessons:
            trade.lessons = lessons

        self._save()
        return trade

    def update(self, trade_id: str, updates: dict) -> TradeEntry | None:
        """Update trade details."""
        trade = self._trades.get(trade_id)
        if not trade:
            return None

        if "notes" in updates:
            trade.notes = updates["notes"]
        if "tags" in updates:
            trade.tags = updates["tags"]
        if "lessons" in updates:
            trade.lessons = updates["lessons"]
        if "strategy" in updates:
            trade.strategy = updates["strategy"]

        self._save()
        return trade

    def delete(self, trade_id: str) -> bool:
        """Delete a trade entry."""
        if trade_id in self._trades:
            del self._trades[trade_id]
            self._save()
            return True
        return False

    def get_stats(self) -> TradeStats:
        """Calculate trading statistics."""
        closed_trades = self.get_closed_trades()

        if not closed_trades:
            return TradeStats(
                total_trades=len(self._trades),
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                avg_win=0,
                avg_loss=0,
                profit_factor=0,
                total_pnl=0,
                avg_pnl=0,
                best_trade=0,
                worst_trade=0,
                avg_holding_days=0,
            )

        pnls = [t.pnl or 0 for t in closed_trades]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p < 0]

        total_win = sum(winning)
        total_loss = abs(sum(losing))

        # Calculate holding days
        holding_days = []
        for t in closed_trades:
            if t.exit_date:
                days = (t.exit_date - t.entry_date).days
                holding_days.append(max(1, days))

        return TradeStats(
            total_trades=len(self._trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=len(winning) / len(closed_trades) * 100 if closed_trades else 0,
            avg_win=total_win / len(winning) if winning else 0,
            avg_loss=total_loss / len(losing) if losing else 0,
            profit_factor=total_win / total_loss if total_loss > 0 else float("inf"),
            total_pnl=sum(pnls),
            avg_pnl=sum(pnls) / len(pnls) if pnls else 0,
            best_trade=max(pnls) if pnls else 0,
            worst_trade=min(pnls) if pnls else 0,
            avg_holding_days=sum(holding_days) / len(holding_days) if holding_days else 0,
        )

    def get_by_symbol(self, symbol: str) -> list[TradeEntry]:
        """Get all trades for a symbol."""
        return [t for t in self._trades.values() if t.symbol.upper() == symbol.upper()]

    def get_by_strategy(self, strategy: str) -> list[TradeEntry]:
        """Get all trades for a strategy."""
        return [t for t in self._trades.values() if t.strategy.lower() == strategy.lower()]

    def get_by_tag(self, tag: str) -> list[TradeEntry]:
        """Get all trades with a specific tag."""
        return [t for t in self._trades.values() if tag.lower() in [tg.lower() for tg in t.tags]]


# Global service instance
journal_service = JournalService()
