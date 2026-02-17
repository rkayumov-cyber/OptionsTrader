"""Options Trading Decision Engine.

Implements the algorithmic decision-making model synthesized from
Goldman Sachs and JPMorgan derivatives research (2003-2025).
"""

from .engine import DecisionEngine
from .regime import RegimeClassifier
from .sizing import PositionSizer
from .strategies import StrategyUniverse
from .selector import StrategySelector
from .adjustments import AdjustmentEngine
from .exits import ExitEngine
from .playbooks import EventPlaybooks
from .tail_risk import TailRiskManager
from .conflicts import ConflictResolver
from .reference_tables import ReferenceTables
from .market_inputs import MarketInputsCollector

__all__ = [
    "DecisionEngine",
    "RegimeClassifier",
    "PositionSizer",
    "StrategyUniverse",
    "StrategySelector",
    "AdjustmentEngine",
    "ExitEngine",
    "EventPlaybooks",
    "TailRiskManager",
    "ConflictResolver",
    "ReferenceTables",
    "MarketInputsCollector",
]
