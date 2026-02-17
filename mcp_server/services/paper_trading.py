"""Paper trading service."""

import uuid
from datetime import datetime
from mcp_server.models import (
    PaperAccount,
    PaperOrder,
    PaperPosition,
    Market,
    OrderStatus,
)
from .storage import storage


class PaperTradingService:
    """Paper trading account management."""

    ACCOUNTS_KEY = "paper_accounts"

    def __init__(self):
        self._accounts: dict[str, PaperAccount] = {}
        self._load()

    def _load(self):
        """Load accounts from storage."""
        self._accounts = storage.load_dict(self.ACCOUNTS_KEY, PaperAccount)

    def _save(self):
        """Save accounts to storage."""
        storage.save_dict(self.ACCOUNTS_KEY, self._accounts)

    def create_account(self, name: str = "Default", initial_cash: float = 100000.0) -> PaperAccount:
        """Create a new paper trading account."""
        account_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        account = PaperAccount(
            id=account_id,
            name=name,
            initial_cash=initial_cash,
            cash=initial_cash,
            total_value=initial_cash,
            created_at=now,
            last_updated=now,
        )

        self._accounts[account_id] = account
        self._save()
        return account

    def get_account(self, account_id: str) -> PaperAccount | None:
        """Get account by ID."""
        return self._accounts.get(account_id)

    def get_default_account(self) -> PaperAccount:
        """Get or create default account."""
        if not self._accounts:
            return self.create_account()
        return list(self._accounts.values())[0]

    def get_all_accounts(self) -> list[PaperAccount]:
        """Get all accounts."""
        return list(self._accounts.values())

    def place_order(
        self,
        account_id: str,
        symbol: str,
        market: Market,
        side: str,
        quantity: int,
        order_type: str = "market",
        limit_price: float | None = None,
        option_symbol: str | None = None,
    ) -> PaperOrder | None:
        """Place a paper trading order."""
        account = self._accounts.get(account_id)
        if not account:
            return None

        order_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        # For market orders, fill immediately with mock price
        mock_price = limit_price or 150.0  # Mock current price

        order = PaperOrder(
            id=order_id,
            account_id=account_id,
            symbol=symbol,
            market=market,
            option_symbol=option_symbol,
            order_type=order_type,
            side=side,
            quantity=quantity,
            limit_price=limit_price,
            status="pending",
            created_at=now,
        )

        # Auto-fill market orders
        if order_type == "market":
            order = self._fill_order(account, order, mock_price)
        else:
            account.orders.append(order)

        self._accounts[account_id] = account
        self._save()
        return order

    def _fill_order(self, account: PaperAccount, order: PaperOrder, fill_price: float) -> PaperOrder:
        """Fill an order and update positions."""
        now = datetime.now()
        order.status = "filled"
        order.filled_price = fill_price
        order.filled_quantity = order.quantity
        order.filled_at = now

        total_cost = fill_price * order.quantity

        if order.side == "buy":
            # Check buying power
            if account.cash < total_cost:
                order.status = "rejected"
                return order

            account.cash -= total_cost

            # Update or create position
            existing = next(
                (p for p in account.positions if p.symbol == order.symbol and p.option_symbol == order.option_symbol),
                None
            )
            if existing:
                # Average up/down
                total_qty = existing.quantity + order.quantity
                existing.avg_entry_price = (
                    (existing.avg_entry_price * existing.quantity + fill_price * order.quantity) / total_qty
                )
                existing.quantity = total_qty
            else:
                account.positions.append(PaperPosition(
                    symbol=order.symbol,
                    market=order.market,
                    option_symbol=order.option_symbol,
                    quantity=order.quantity,
                    avg_entry_price=fill_price,
                    current_price=fill_price,
                ))
        else:  # sell
            existing = next(
                (p for p in account.positions if p.symbol == order.symbol and p.option_symbol == order.option_symbol),
                None
            )
            if existing and existing.quantity >= order.quantity:
                account.cash += total_cost
                pnl = (fill_price - existing.avg_entry_price) * order.quantity
                existing.realized_pnl += pnl
                existing.quantity -= order.quantity

                if existing.quantity == 0:
                    account.positions.remove(existing)
            else:
                order.status = "rejected"
                return order

        # Update account totals
        self._update_account_totals(account)
        account.orders.append(order)
        account.last_updated = now

        return order

    def _update_account_totals(self, account: PaperAccount):
        """Update account total value and P/L."""
        positions_value = sum(
            (p.current_price or p.avg_entry_price) * p.quantity
            for p in account.positions
        )
        account.total_value = account.cash + positions_value
        account.total_pnl = account.total_value - account.initial_cash
        account.total_pnl_percent = (account.total_pnl / account.initial_cash) * 100

    def update_prices(self, account_id: str, prices: dict[str, float]):
        """Update position prices."""
        account = self._accounts.get(account_id)
        if not account:
            return

        for position in account.positions:
            key = position.option_symbol or position.symbol
            if key in prices:
                position.current_price = prices[key]
                position.unrealized_pnl = (
                    (position.current_price - position.avg_entry_price) * position.quantity
                )

        self._update_account_totals(account)
        account.last_updated = datetime.now()
        self._save()

    def get_positions(self, account_id: str) -> list[PaperPosition]:
        """Get positions for an account."""
        account = self._accounts.get(account_id)
        return account.positions if account else []

    def get_orders(self, account_id: str) -> list[PaperOrder]:
        """Get orders for an account."""
        account = self._accounts.get(account_id)
        return account.orders if account else []

    def cancel_order(self, account_id: str, order_id: str) -> bool:
        """Cancel a pending order."""
        account = self._accounts.get(account_id)
        if not account:
            return False

        for order in account.orders:
            if order.id == order_id and order.status == "pending":
                order.status = "cancelled"
                self._save()
                return True
        return False

    def reset_account(self, account_id: str) -> PaperAccount | None:
        """Reset account to initial state."""
        account = self._accounts.get(account_id)
        if not account:
            return None

        now = datetime.now()
        account.cash = account.initial_cash
        account.positions = []
        account.orders = []
        account.total_value = account.initial_cash
        account.total_pnl = 0
        account.total_pnl_percent = 0
        account.last_updated = now

        self._save()
        return account


# Global service instance
paper_trading_service = PaperTradingService()
