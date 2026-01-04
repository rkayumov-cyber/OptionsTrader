"""Data models for market data."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


Market = Literal["US", "JP", "HK"]
OptionType = Literal["call", "put"]


class Greeks(BaseModel):
    """Option Greeks."""

    delta: float = Field(description="Rate of change of option price vs underlying")
    gamma: float = Field(description="Rate of change of delta")
    theta: float = Field(description="Time decay per day")
    vega: float = Field(description="Sensitivity to volatility")
    rho: float = Field(description="Sensitivity to interest rate")


class Quote(BaseModel):
    """Real-time price quote."""

    symbol: str
    market: Market
    price: float
    bid: float | None = None
    ask: float | None = None
    volume: int = 0
    timestamp: datetime


class OptionContract(BaseModel):
    """Single option contract."""

    symbol: str
    underlying: str
    strike: float
    expiration: date
    option_type: OptionType
    bid: float | None = None
    ask: float | None = None
    last_price: float | None = None
    volume: int = 0
    open_interest: int = 0
    implied_volatility: float | None = None
    greeks: Greeks | None = None


class OptionChain(BaseModel):
    """Option chain for a symbol."""

    underlying: str
    market: Market
    expirations: list[date]
    calls: list[OptionContract]
    puts: list[OptionContract]
    timestamp: datetime


class VolatilitySurface(BaseModel):
    """Implied volatility surface."""

    symbol: str
    market: Market
    strikes: list[float]
    expirations: list[date]
    call_ivs: list[list[float]]  # 2D grid [expiration][strike]
    put_ivs: list[list[float]]  # 2D grid [expiration][strike]
    timestamp: datetime


class MarketInfo(BaseModel):
    """Market information."""

    code: Market
    name: str
    currency: str
    timezone: str
    trading_hours: str
    is_open: bool = False


class WatchlistItem(BaseModel):
    """Watchlist entry."""

    symbol: str
    market: Market
    name: str | None = None
    added_at: datetime
