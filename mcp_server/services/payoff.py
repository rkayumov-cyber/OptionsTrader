"""Payoff diagram calculator with time decay support."""

import math
from scipy.stats import norm
from mcp_server.models import PayoffLeg, PayoffPoint, PayoffResult


class PayoffCalculator:
    """Calculate option payoff diagrams with time decay visualization."""

    @staticmethod
    def black_scholes_price(
        spot: float,
        strike: float,
        dte: float,
        iv: float,
        rate: float,
        option_type: str,
    ) -> float:
        """Calculate Black-Scholes option price.

        Args:
            spot: Current underlying price
            strike: Option strike price
            dte: Days to expiration
            iv: Implied volatility (decimal, e.g., 0.30 for 30%)
            rate: Risk-free rate (decimal, e.g., 0.05 for 5%)
            option_type: 'call' or 'put'

        Returns:
            Theoretical option price
        """
        if dte <= 0:
            # At expiration, return intrinsic value
            if option_type == "call":
                return max(0, spot - strike)
            else:
                return max(0, strike - spot)

        t = dte / 365.0  # Convert days to years

        # Handle edge cases
        if iv <= 0 or t <= 0:
            if option_type == "call":
                return max(0, spot - strike)
            else:
                return max(0, strike - spot)

        try:
            d1 = (math.log(spot / strike) + (rate + 0.5 * iv ** 2) * t) / (iv * math.sqrt(t))
            d2 = d1 - iv * math.sqrt(t)

            if option_type == "call":
                price = spot * norm.cdf(d1) - strike * math.exp(-rate * t) * norm.cdf(d2)
            else:
                price = strike * math.exp(-rate * t) * norm.cdf(-d2) - spot * norm.cdf(-d1)

            return max(0, price)
        except (ValueError, ZeroDivisionError):
            # Fallback to intrinsic value
            if option_type == "call":
                return max(0, spot - strike)
            else:
                return max(0, strike - spot)

    @staticmethod
    def calculate_leg_pnl(leg: PayoffLeg, price: float) -> float:
        """Calculate P/L for a single leg at expiration."""
        intrinsic = 0.0

        if leg.option_type == "call":
            intrinsic = max(0, price - leg.strike)
        else:  # put
            intrinsic = max(0, leg.strike - price)

        # Per contract P/L
        if leg.action == "buy":
            pnl = (intrinsic - leg.premium) * leg.quantity * 100
        else:  # sell
            pnl = (leg.premium - intrinsic) * leg.quantity * 100

        return pnl

    @staticmethod
    def calculate_leg_pnl_with_time(
        leg: PayoffLeg,
        price: float,
        dte: float,
        iv: float = 0.30,
        rate: float = 0.05,
    ) -> float:
        """Calculate P/L for a single leg at a specific DTE.

        Args:
            leg: The option leg
            price: Current underlying price
            dte: Days to expiration remaining
            iv: Implied volatility (default 30%)
            rate: Risk-free rate (default 5%)

        Returns:
            P/L in dollars
        """
        # Calculate theoretical value at this DTE
        theoretical_value = PayoffCalculator.black_scholes_price(
            spot=price,
            strike=leg.strike,
            dte=dte,
            iv=iv,
            rate=rate,
            option_type=leg.option_type,
        )

        # Calculate P/L based on entry premium
        if leg.action == "buy":
            pnl = (theoretical_value - leg.premium) * leg.quantity * 100
        else:  # sell
            pnl = (leg.premium - theoretical_value) * leg.quantity * 100

        return pnl

    @staticmethod
    def calculate_payoff(
        legs: list[PayoffLeg],
        underlying_price: float,
        price_range_percent: float = 30,
        num_points: int = 100,
    ) -> PayoffResult:
        """Calculate payoff diagram for a set of legs at expiration."""
        if not legs:
            return PayoffResult(
                underlying_price=underlying_price,
                legs=legs,
                points=[],
                breakevens=[],
                max_profit=0,
                max_loss=0,
                net_premium=0,
            )

        # Calculate net premium
        net_premium = 0.0
        for leg in legs:
            if leg.action == "buy":
                net_premium -= leg.premium * leg.quantity * 100
            else:
                net_premium += leg.premium * leg.quantity * 100

        # Generate price range
        min_price = underlying_price * (1 - price_range_percent / 100)
        max_price = underlying_price * (1 + price_range_percent / 100)
        price_step = (max_price - min_price) / num_points

        # Calculate P/L at each price point
        points: list[PayoffPoint] = []
        all_pnls: list[float] = []

        for i in range(num_points + 1):
            price = min_price + i * price_step
            leg_pnls = [PayoffCalculator.calculate_leg_pnl(leg, price) for leg in legs]
            total_pnl = sum(leg_pnls)
            points.append(PayoffPoint(price=round(price, 2), pnl=round(total_pnl, 2), leg_pnls=leg_pnls))
            all_pnls.append(total_pnl)

        # Find breakevens (where P/L crosses zero)
        breakevens: list[float] = []
        for i in range(len(points) - 1):
            if (points[i].pnl <= 0 <= points[i + 1].pnl) or (points[i].pnl >= 0 >= points[i + 1].pnl):
                # Linear interpolation to find exact breakeven
                if points[i + 1].pnl != points[i].pnl:
                    ratio = -points[i].pnl / (points[i + 1].pnl - points[i].pnl)
                    breakeven = points[i].price + ratio * (points[i + 1].price - points[i].price)
                    breakevens.append(round(breakeven, 2))

        # Calculate max profit and max loss
        max_profit = max(all_pnls) if all_pnls else 0
        max_loss = min(all_pnls) if all_pnls else 0

        # Check for unlimited profit/loss
        if len(all_pnls) >= 2:
            if all_pnls[-1] > all_pnls[-2] and all_pnls[-1] == max_profit:
                max_profit = None  # Unlimited upside
            if all_pnls[0] < all_pnls[1] and all_pnls[0] == max_loss:
                max_loss = None  # Unlimited downside

        return PayoffResult(
            underlying_price=underlying_price,
            legs=legs,
            points=points,
            breakevens=breakevens,
            max_profit=max_profit,
            max_loss=max_loss,
            net_premium=round(net_premium, 2),
        )

    @staticmethod
    def calculate_payoff_with_time(
        legs: list[PayoffLeg],
        underlying_price: float,
        dte: float,
        iv: float = 0.30,
        rate: float = 0.05,
        price_range_percent: float = 30,
        num_points: int = 100,
    ) -> PayoffResult:
        """Calculate payoff diagram at a specific DTE (not at expiration).

        Args:
            legs: List of option legs
            underlying_price: Current underlying price
            dte: Days to expiration
            iv: Implied volatility (decimal)
            rate: Risk-free rate (decimal)
            price_range_percent: Price range for diagram
            num_points: Number of price points to calculate

        Returns:
            PayoffResult with P/L at each price point for the given DTE
        """
        if not legs:
            return PayoffResult(
                underlying_price=underlying_price,
                legs=legs,
                points=[],
                breakevens=[],
                max_profit=0,
                max_loss=0,
                net_premium=0,
            )

        # Calculate net premium
        net_premium = 0.0
        for leg in legs:
            if leg.action == "buy":
                net_premium -= leg.premium * leg.quantity * 100
            else:
                net_premium += leg.premium * leg.quantity * 100

        # Generate price range
        min_price = underlying_price * (1 - price_range_percent / 100)
        max_price = underlying_price * (1 + price_range_percent / 100)
        price_step = (max_price - min_price) / num_points

        # Calculate P/L at each price point
        points: list[PayoffPoint] = []
        all_pnls: list[float] = []

        for i in range(num_points + 1):
            price = min_price + i * price_step
            leg_pnls = [
                PayoffCalculator.calculate_leg_pnl_with_time(leg, price, dte, iv, rate)
                for leg in legs
            ]
            total_pnl = sum(leg_pnls)
            points.append(PayoffPoint(price=round(price, 2), pnl=round(total_pnl, 2), leg_pnls=leg_pnls))
            all_pnls.append(total_pnl)

        # Find breakevens
        breakevens: list[float] = []
        for i in range(len(points) - 1):
            if (points[i].pnl <= 0 <= points[i + 1].pnl) or (points[i].pnl >= 0 >= points[i + 1].pnl):
                if points[i + 1].pnl != points[i].pnl:
                    ratio = -points[i].pnl / (points[i + 1].pnl - points[i].pnl)
                    breakeven = points[i].price + ratio * (points[i + 1].price - points[i].price)
                    breakevens.append(round(breakeven, 2))

        max_profit = max(all_pnls) if all_pnls else 0
        max_loss = min(all_pnls) if all_pnls else 0

        return PayoffResult(
            underlying_price=underlying_price,
            legs=legs,
            points=points,
            breakevens=breakevens,
            max_profit=max_profit,
            max_loss=max_loss,
            net_premium=round(net_premium, 2),
        )

    @staticmethod
    def calculate_time_series_payoff(
        legs: list[PayoffLeg],
        underlying_price: float,
        max_dte: int = 30,
        iv: float = 0.30,
        rate: float = 0.05,
        price_range_percent: float = 30,
        num_points: int = 50,
        time_intervals: list[int] | None = None,
    ) -> dict:
        """Calculate payoff curves for multiple time points.

        Args:
            legs: List of option legs
            underlying_price: Current underlying price
            max_dte: Maximum days to expiration
            iv: Implied volatility
            rate: Risk-free rate
            price_range_percent: Price range for diagram
            num_points: Number of price points
            time_intervals: Specific DTE values to calculate (default: [0, 7, 14, 21, max_dte])

        Returns:
            Dictionary with time series payoff data
        """
        if time_intervals is None:
            # Default time intervals
            if max_dte <= 7:
                time_intervals = [0, 1, 3, 5, max_dte]
            elif max_dte <= 30:
                time_intervals = [0, 7, 14, 21, max_dte]
            elif max_dte <= 60:
                time_intervals = [0, 15, 30, 45, max_dte]
            else:
                time_intervals = [0, 30, 60, 90, max_dte]

        # Remove duplicates and sort
        time_intervals = sorted(set(time_intervals))

        # Calculate expiration payoff (DTE=0)
        expiration_result = PayoffCalculator.calculate_payoff(
            legs=legs,
            underlying_price=underlying_price,
            price_range_percent=price_range_percent,
            num_points=num_points,
        )

        # Calculate payoff for each time interval
        time_curves = []
        for dte in time_intervals:
            if dte == 0:
                # Use expiration calculation
                curve_data = {
                    "dte": 0,
                    "label": "Expiration",
                    "points": [{"price": p.price, "pnl": p.pnl} for p in expiration_result.points],
                    "breakevens": expiration_result.breakevens,
                }
            else:
                result = PayoffCalculator.calculate_payoff_with_time(
                    legs=legs,
                    underlying_price=underlying_price,
                    dte=dte,
                    iv=iv,
                    rate=rate,
                    price_range_percent=price_range_percent,
                    num_points=num_points,
                )
                curve_data = {
                    "dte": dte,
                    "label": f"{dte}D" if dte < 30 else f"{dte // 30}M",
                    "points": [{"price": p.price, "pnl": p.pnl} for p in result.points],
                    "breakevens": result.breakevens,
                }
            time_curves.append(curve_data)

        # Calculate net premium
        net_premium = 0.0
        for leg in legs:
            if leg.action == "buy":
                net_premium -= leg.premium * leg.quantity * 100
            else:
                net_premium += leg.premium * leg.quantity * 100

        return {
            "underlying_price": underlying_price,
            "legs": [leg.model_dump() for leg in legs],
            "time_curves": time_curves,
            "max_dte": max_dte,
            "iv": iv,
            "rate": rate,
            "max_profit": expiration_result.max_profit,
            "max_loss": expiration_result.max_loss,
            "net_premium": round(net_premium, 2),
            "expiration_breakevens": expiration_result.breakevens,
        }

    @staticmethod
    def get_strategy_template(
        strategy: str,
        underlying_price: float,
        atm_strike: float | None = None,
    ) -> list[PayoffLeg]:
        """Get predefined strategy leg templates."""
        if atm_strike is None:
            atm_strike = round(underlying_price / 5) * 5  # Round to nearest 5

        strike_width = atm_strike * 0.05  # 5% OTM

        templates = {
            "long_call": [
                PayoffLeg(option_type="call", action="buy", strike=atm_strike, quantity=1, premium=5.0)
            ],
            "long_put": [
                PayoffLeg(option_type="put", action="buy", strike=atm_strike, quantity=1, premium=5.0)
            ],
            "covered_call": [
                PayoffLeg(option_type="call", action="sell", strike=atm_strike + strike_width, quantity=1, premium=3.0)
            ],
            "bull_call_spread": [
                PayoffLeg(option_type="call", action="buy", strike=atm_strike, quantity=1, premium=5.0),
                PayoffLeg(option_type="call", action="sell", strike=atm_strike + strike_width, quantity=1, premium=2.0),
            ],
            "bear_put_spread": [
                PayoffLeg(option_type="put", action="buy", strike=atm_strike, quantity=1, premium=5.0),
                PayoffLeg(option_type="put", action="sell", strike=atm_strike - strike_width, quantity=1, premium=2.0),
            ],
            "long_straddle": [
                PayoffLeg(option_type="call", action="buy", strike=atm_strike, quantity=1, premium=5.0),
                PayoffLeg(option_type="put", action="buy", strike=atm_strike, quantity=1, premium=5.0),
            ],
            "short_straddle": [
                PayoffLeg(option_type="call", action="sell", strike=atm_strike, quantity=1, premium=5.0),
                PayoffLeg(option_type="put", action="sell", strike=atm_strike, quantity=1, premium=5.0),
            ],
            "long_strangle": [
                PayoffLeg(option_type="call", action="buy", strike=atm_strike + strike_width, quantity=1, premium=3.0),
                PayoffLeg(option_type="put", action="buy", strike=atm_strike - strike_width, quantity=1, premium=3.0),
            ],
            "iron_condor": [
                PayoffLeg(option_type="put", action="buy", strike=atm_strike - strike_width * 2, quantity=1, premium=1.0),
                PayoffLeg(option_type="put", action="sell", strike=atm_strike - strike_width, quantity=1, premium=2.5),
                PayoffLeg(option_type="call", action="sell", strike=atm_strike + strike_width, quantity=1, premium=2.5),
                PayoffLeg(option_type="call", action="buy", strike=atm_strike + strike_width * 2, quantity=1, premium=1.0),
            ],
            "iron_butterfly": [
                PayoffLeg(option_type="put", action="buy", strike=atm_strike - strike_width, quantity=1, premium=2.0),
                PayoffLeg(option_type="put", action="sell", strike=atm_strike, quantity=1, premium=5.0),
                PayoffLeg(option_type="call", action="sell", strike=atm_strike, quantity=1, premium=5.0),
                PayoffLeg(option_type="call", action="buy", strike=atm_strike + strike_width, quantity=1, premium=2.0),
            ],
        }

        return templates.get(strategy, [])


# Global calculator instance
payoff_calculator = PayoffCalculator()
