"""Position tracking service."""

import uuid
from datetime import datetime
from mcp_server.models import (
    Position,
    PositionLeg,
    PortfolioSummary,
    Greeks,
    Market,
)
from .storage import storage


class PositionService:
    """Manage tracked positions."""

    STORAGE_KEY = "positions"

    def __init__(self):
        self._positions: dict[str, Position] = {}
        self._load()

    def _load(self):
        """Load positions from storage."""
        self._positions = storage.load_dict(self.STORAGE_KEY, Position)

    def _save(self):
        """Save positions to storage."""
        storage.save_dict(self.STORAGE_KEY, self._positions)

    def get_all(self) -> list[Position]:
        """Get all positions."""
        return list(self._positions.values())

    def get_open(self) -> list[Position]:
        """Get open positions only."""
        return [p for p in self._positions.values() if p.status == "open"]

    def get_by_id(self, position_id: str) -> Position | None:
        """Get position by ID."""
        return self._positions.get(position_id)

    def create(
        self,
        symbol: str,
        market: Market,
        legs: list[PositionLeg],
        strategy_name: str = "Custom",
        notes: str = "",
    ) -> Position:
        """Create a new position."""
        position_id = str(uuid.uuid4())[:8]

        # Calculate entry cost
        entry_cost = 0.0
        for leg in legs:
            if leg.action == "buy":
                entry_cost -= leg.entry_premium * leg.quantity * 100
            else:
                entry_cost += leg.entry_premium * leg.quantity * 100

        position = Position(
            id=position_id,
            symbol=symbol,
            market=market,
            strategy_name=strategy_name,
            legs=legs,
            entry_date=datetime.now(),
            entry_cost=entry_cost,
            status="open",
            notes=notes,
        )

        self._positions[position_id] = position
        self._save()
        return position

    def update(self, position_id: str, updates: dict) -> Position | None:
        """Update a position."""
        position = self._positions.get(position_id)
        if not position:
            return None

        # Update allowed fields
        if "notes" in updates:
            position.notes = updates["notes"]
        if "current_value" in updates:
            position.current_value = updates["current_value"]
            if position.entry_cost != 0:
                position.pnl = position.current_value - position.entry_cost
                position.pnl_percent = (position.pnl / abs(position.entry_cost)) * 100
        if "status" in updates:
            position.status = updates["status"]
        if "greeks" in updates:
            position.greeks = Greeks(**updates["greeks"])

        self._positions[position_id] = position
        self._save()
        return position

    def close(self, position_id: str, exit_value: float | None = None) -> Position | None:
        """Close a position."""
        position = self._positions.get(position_id)
        if not position:
            return None

        position.status = "closed"
        if exit_value is not None:
            position.current_value = exit_value
            position.pnl = exit_value - position.entry_cost
            if position.entry_cost != 0:
                position.pnl_percent = (position.pnl / abs(position.entry_cost)) * 100

        self._positions[position_id] = position
        self._save()
        return position

    def delete(self, position_id: str) -> bool:
        """Delete a position."""
        if position_id in self._positions:
            del self._positions[position_id]
            self._save()
            return True
        return False

    def get_summary(self) -> PortfolioSummary:
        """Get portfolio summary with aggregated Greeks."""
        positions = list(self._positions.values())
        open_positions = [p for p in positions if p.status == "open"]

        total_value = sum(p.current_value or 0 for p in open_positions)
        total_cost = sum(p.entry_cost for p in open_positions)
        total_pnl = sum(p.pnl or 0 for p in open_positions)

        # Aggregate Greeks
        agg_delta = sum(p.greeks.delta if p.greeks else 0 for p in open_positions)
        agg_gamma = sum(p.greeks.gamma if p.greeks else 0 for p in open_positions)
        agg_theta = sum(p.greeks.theta if p.greeks else 0 for p in open_positions)
        agg_vega = sum(p.greeks.vega if p.greeks else 0 for p in open_positions)

        return PortfolioSummary(
            total_positions=len(positions),
            open_positions=len(open_positions),
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_percent=(total_pnl / abs(total_cost) * 100) if total_cost != 0 else 0,
            aggregate_delta=agg_delta,
            aggregate_gamma=agg_gamma,
            aggregate_theta=agg_theta,
            aggregate_vega=agg_vega,
        )


# Global service instance
position_service = PositionService()
