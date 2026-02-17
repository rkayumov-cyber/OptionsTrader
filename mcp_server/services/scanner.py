"""Options scanner service."""

import random
from datetime import datetime
from mcp_server.models import (
    ScanCriteria,
    ScanResult,
    ScanResponse,
    Market,
    Sentiment,
)


# Sample symbols for scanning
SCAN_SYMBOLS = {
    "US": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "NFLX", "SPY", "QQQ", "IWM", "DIA", "XLF", "XLE"],
    "JP": ["7203", "6758", "9984", "6861", "7267"],
    "HK": ["0700", "9988", "1299", "0005", "0941"],
}


class ScannerService:
    """Options scanner for finding opportunities."""

    @staticmethod
    def scan(criteria: ScanCriteria) -> ScanResponse:
        """Scan for options matching criteria."""
        symbols = criteria.symbols or SCAN_SYMBOLS.get(criteria.market, [])
        results: list[ScanResult] = []

        for symbol in symbols:
            # Generate mock scan data
            iv_rank = random.uniform(10, 90)
            iv_percentile = random.uniform(10, 90)
            pc_ratio = random.uniform(0.5, 1.5)
            volume = random.randint(10000, 500000)
            oi = random.randint(50000, 2000000)
            price = random.uniform(50, 500)

            # Apply filters
            if criteria.iv_rank_min is not None and iv_rank < criteria.iv_rank_min:
                continue
            if criteria.iv_rank_max is not None and iv_rank > criteria.iv_rank_max:
                continue
            if criteria.volume_min is not None and volume < criteria.volume_min:
                continue
            if criteria.open_interest_min is not None and oi < criteria.open_interest_min:
                continue

            # Determine sentiment
            if pc_ratio < 0.7:
                sentiment: Sentiment = "bullish"
            elif pc_ratio < 0.9:
                sentiment = "slightly_bullish"
            elif pc_ratio < 1.1:
                sentiment = "neutral"
            elif pc_ratio < 1.3:
                sentiment = "slightly_bearish"
            else:
                sentiment = "bearish"

            # Calculate composite score
            score = 50.0
            if iv_rank > 70:
                score += 20  # High IV is good for selling
            elif iv_rank < 30:
                score += 15  # Low IV is good for buying
            if volume > 100000:
                score += 10
            if oi > 500000:
                score += 5
            score = min(100, max(0, score + random.uniform(-10, 10)))

            results.append(ScanResult(
                symbol=symbol,
                market=criteria.market,
                price=round(price, 2),
                iv_rank=round(iv_rank, 1),
                iv_percentile=round(iv_percentile, 1),
                put_call_ratio=round(pc_ratio, 2),
                total_volume=volume,
                total_open_interest=oi,
                sentiment=sentiment,
                score=round(score, 1),
            ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return ScanResponse(
            criteria=criteria,
            results=results[:20],  # Top 20 results
            total_scanned=len(symbols),
            timestamp=datetime.now(),
        )

    @staticmethod
    def get_high_iv_opportunities(market: Market = "US") -> ScanResponse:
        """Find high IV rank opportunities (premium selling)."""
        return ScannerService.scan(ScanCriteria(
            market=market,
            iv_rank_min=70,
            volume_min=50000,
        ))

    @staticmethod
    def get_low_iv_opportunities(market: Market = "US") -> ScanResponse:
        """Find low IV rank opportunities (premium buying)."""
        return ScannerService.scan(ScanCriteria(
            market=market,
            iv_rank_max=30,
            volume_min=50000,
        ))

    @staticmethod
    def get_high_volume_activity(market: Market = "US") -> ScanResponse:
        """Find high volume activity."""
        return ScannerService.scan(ScanCriteria(
            market=market,
            volume_min=200000,
        ))


# Global service instance
scanner_service = ScannerService()
