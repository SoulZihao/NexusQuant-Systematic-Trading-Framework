from factors.base import BaseFactor
from factors.supertrend import SuperTrendFactor
from factors.bollinger import BollingerFactor
from factors.rsi import RSIFactor
from factors.macd import MACDFactor
from factors.obv import OBVFactor

ALL_FACTORS = [
    SuperTrendFactor(),
    BollingerFactor(),
    RSIFactor(),
    MACDFactor(),
    OBVFactor(),
]
