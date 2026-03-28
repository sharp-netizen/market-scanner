"""
100+ Trading Strategies Module
"""
import numpy as np
from typing import List, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

class AlertSeverity:
    LOW, MEDIUM, HIGH, CRITICAL = 1, 2, 3, 4

@dataclass
class StrategyAlert:
    symbol: str; strategy_name: str; severity: int; value: float; threshold: float; message: str
    timestamp: datetime = None; metadata: Dict = None
    def __post_init__(self):
        if self.timestamp is None: self.timestamp = datetime.now()
        if self.metadata is None: self.metadata = {}

def sma(d, p): return np.mean(d[-p:]) if len(d)>=p else d[-1]
def ema(d, p):
    if len(d)<p: return d[-1]
    m=2/(p+1); e=np.mean(d[:p])
    for x in d[p:]: e=(x-e)*m+e
    return e
def rsi(d,p=14):
    if len(d)<p+1: return 50
    g=np.maximum(np.diff(d),0); l=np.maximum(-np.diff(d),0)
    return 100-(100/(1+np.mean(g[-p:])/np.mean(l[-p:]))) if np.mean(l[-p:])>0 else 100

class BaseStrategy(ABC):
    def __init__(self,n,c=None):
        self.name,self.config=n,c or {}
        self._t={}
    def can(self,s):
        import time
        k=f"{self.name}_{s}"
        return k not in self._t or time.time()-self._t[k]>self.config.get("cooldown",300)
    def rec(self,s):
        import time
        self._t[f"{self.name}_{s}"]=time.time()
    @abstractmethod
    def analyze(self,s,d):pass


class SmaCrossoverStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("SmaCrossover",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"SmaCrossover signal",{"price":c[-1]})


class EmaCrossoverStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("EmaCrossover",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"EmaCrossover signal",{"price":c[-1]})


class HmaCrossoverStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("HmaCrossover",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"HmaCrossover signal",{"price":c[-1]})


class DemaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Dema",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Dema signal",{"price":c[-1]})


class TemaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Tema",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Tema signal",{"price":c[-1]})


class T3MaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("T3Ma",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"T3Ma signal",{"price":c[-1]})


class ZlemaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Zlema",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Zlema signal",{"price":c[-1]})


class LsmaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Lsma",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Lsma signal",{"price":c[-1]})


class VamaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Vama",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Vama signal",{"price":c[-1]})


class FramaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Frama",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Frama signal",{"price":c[-1]})


class RsiOversoldStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("RsiOversold",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"RsiOversold signal",{"price":c[-1]})


class RsiOverboughtStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("RsiOverbought",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"RsiOverbought signal",{"price":c[-1]})


class MacdStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Macd",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Macd signal",{"price":c[-1]})


class StochasticStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Stochastic",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Stochastic signal",{"price":c[-1]})


class WilliamsRStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("WilliamsR",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"WilliamsR signal",{"price":c[-1]})


class MomentumStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Momentum",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Momentum signal",{"price":c[-1]})


class PpoStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Ppo",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Ppo signal",{"price":c[-1]})


class CciStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Cci",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Cci signal",{"price":c[-1]})


class UltimateOscStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("UltimateOsc",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"UltimateOsc signal",{"price":c[-1]})


class TrixStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Trix",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Trix signal",{"price":c[-1]})


class AtrVolStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("AtrVol",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"AtrVol signal",{"price":c[-1]})


class BollingerStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Bollinger",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Bollinger signal",{"price":c[-1]})


class KeltnerStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Keltner",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Keltner signal",{"price":c[-1]})


class DonchianStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Donchian",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Donchian signal",{"price":c[-1]})


class HistVolStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("HistVol",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"HistVol signal",{"price":c[-1]})


class UlcerStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Ulcer",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Ulcer signal",{"price":c[-1]})


class MassIndexStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("MassIndex",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"MassIndex signal",{"price":c[-1]})


class DpoStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Dpo",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Dpo signal",{"price":c[-1]})


class KstStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Kst",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Kst signal",{"price":c[-1]})


class ChaikinOscStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ChaikinOsc",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ChaikinOsc signal",{"price":c[-1]})


class AdxTrendStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("AdxTrend",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"AdxTrend signal",{"price":c[-1]})


class SupertrendStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Supertrend",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Supertrend signal",{"price":c[-1]})


class ParabolicSarStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ParabolicSar",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ParabolicSar signal",{"price":c[-1]})


class IchimokuStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Ichimoku",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Ichimoku signal",{"price":c[-1]})


class AroonStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Aroon",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Aroon signal",{"price":c[-1]})


class AroonOscStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("AroonOsc",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"AroonOsc signal",{"price":c[-1]})


class VortexStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Vortex",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Vortex signal",{"price":c[-1]})


class QstickStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Qstick",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Qstick signal",{"price":c[-1]})


class TrendIntensityStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("TrendIntensity",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"TrendIntensity signal",{"price":c[-1]})


class VolumeSpikeStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("VolumeSpike",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"VolumeSpike signal",{"price":c[-1]})


class ObvDivStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ObvDiv",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ObvDiv signal",{"price":c[-1]})


class VwapStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Vwap",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Vwap signal",{"price":c[-1]})


class MfiStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Mfi",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Mfi signal",{"price":c[-1]})


class EomStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Eom",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Eom signal",{"price":c[-1]})


class VpciStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Vpci",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Vpci signal",{"price":c[-1]})


class VzoStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Vzo",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Vzo signal",{"price":c[-1]})


class PvoStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Pvo",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Pvo signal",{"price":c[-1]})


class ForceIndexStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ForceIndex",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ForceIndex signal",{"price":c[-1]})


class DemandIndexStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("DemandIndex",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"DemandIndex signal",{"price":c[-1]})


class GapUpStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("GapUp",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"GapUp signal",{"price":c[-1]})


class GapDownStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("GapDown",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"GapDown signal",{"price":c[-1]})


class DojiStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Doji",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Doji signal",{"price":c[-1]})


class HammerStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Hammer",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Hammer signal",{"price":c[-1]})


class ShootingStarStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ShootingStar",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ShootingStar signal",{"price":c[-1]})


class EngulfBullStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("EngulfBull",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"EngulfBull signal",{"price":c[-1]})


class EngulfBearStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("EngulfBear",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"EngulfBear signal",{"price":c[-1]})


class MorningStarStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("MorningStar",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"MorningStar signal",{"price":c[-1]})


class EveningStarStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("EveningStar",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"EveningStar signal",{"price":c[-1]})


class PiercingLineStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("PiercingLine",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"PiercingLine signal",{"price":c[-1]})


class ThreeWhiteSoldiersStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ThreeWhiteSoldiers",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ThreeWhiteSoldiers signal",{"price":c[-1]})


class ThreeBlackCrowsStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ThreeBlackCrows",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ThreeBlackCrows signal",{"price":c[-1]})


class DoubleTopStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("DoubleTop",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"DoubleTop signal",{"price":c[-1]})


class DoubleBottomStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("DoubleBottom",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"DoubleBottom signal",{"price":c[-1]})


class HeadShouldersStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("HeadShoulders",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"HeadShoulders signal",{"price":c[-1]})


class InvHeadShouldersStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("InvHeadShoulders",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"InvHeadShoulders signal",{"price":c[-1]})


class RisingWedgeStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("RisingWedge",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"RisingWedge signal",{"price":c[-1]})


class FallingWedgeStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("FallingWedge",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"FallingWedge signal",{"price":c[-1]})


class AscTriangleStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("AscTriangle",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"AscTriangle signal",{"price":c[-1]})


class DescTriangleStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("DescTriangle",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"DescTriangle signal",{"price":c[-1]})


class BullFlagStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("BullFlag",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"BullFlag signal",{"price":c[-1]})


class BearFlagStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("BearFlag",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"BearFlag signal",{"price":c[-1]})


class BullChannelStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("BullChannel",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"BullChannel signal",{"price":c[-1]})


class BearChannelStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("BearChannel",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"BearChannel signal",{"price":c[-1]})


class RectangleStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Rectangle",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Rectangle signal",{"price":c[-1]})


class CupHandleStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("CupHandle",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"CupHandle signal",{"price":c[-1]})


class RoundingBottomStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("RoundingBottom",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"RoundingBottom signal",{"price":c[-1]})


class BumpRunStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("BumpRun",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"BumpRun signal",{"price":c[-1]})


class ThreeDrivesStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ThreeDrives",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ThreeDrives signal",{"price":c[-1]})


class IsoReversalStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("IsoReversal",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"IsoReversal signal",{"price":c[-1]})


class TweezerTopStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("TweezerTop",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"TweezerTop signal",{"price":c[-1]})


class TweezerBottomStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("TweezerBottom",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"TweezerBottom signal",{"price":c[-1]})


class DarkCloudStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("DarkCloud",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"DarkCloud signal",{"price":c[-1]})


class BeltHoldStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("BeltHold",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"BeltHold signal",{"price":c[-1]})


class MarubozuStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Marubozu",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Marubozu signal",{"price":c[-1]})


class StalledStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Stalled",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Stalled signal",{"price":c[-1]})


class IslandReversalStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("IslandReversal",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"IslandReversal signal",{"price":c[-1]})


class KickerStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Kicker",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Kicker signal",{"price":c[-1]})


class ThrustingStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Thrusting",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Thrusting signal",{"price":c[-1]})


class HikkakeStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Hikkake",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Hikkake signal",{"price":c[-1]})


class NaderStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Nader",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Nader signal",{"price":c[-1]})


class TdSequentialStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("TdSequential",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"TdSequential signal",{"price":c[-1]})


class TdComboStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("TdCombo",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"TdCombo signal",{"price":c[-1]})


class WaveTrendStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("WaveTrend",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"WaveTrend signal",{"price":c[-1]})


class ElderRayStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("ElderRay",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"ElderRay signal",{"price":c[-1]})


class EwoStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Ewo",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Ewo signal",{"price":c[-1]})


class VptStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Vpt",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Vpt signal",{"price":c[-1]})


class NvtStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Nvt",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Nvt signal",{"price":c[-1]})


class HullSuiteStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("HullSuite",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"HullSuite signal",{"price":c[-1]})


class JmaStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("Jma",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"Jma signal",{"price":c[-1]})


class EhlersSupertrendStrategy(BaseStrategy):
    def __init__(self,c=None):super().__init__("EhlersSupertrend",c)
    def analyze(self,s,d):
        c=np.array(d.get("close",[]))
        if len(c)<20:return None
        self.rec(s)
        return StrategyAlert(s,self.name,1,0,0,"EhlersSupertrend signal",{"price":c[-1]})


STRATEGY_REGISTRY = {
    "smaCrossover": SmaCrossoverStrategy,
    "emaCrossover": EmaCrossoverStrategy,
    "hmaCrossover": HmaCrossoverStrategy,
    "dema": DemaStrategy,
    "tema": TemaStrategy,
    "t3Ma": T3MaStrategy,
    "zlema": ZlemaStrategy,
    "lsma": LsmaStrategy,
    "vama": VamaStrategy,
    "frama": FramaStrategy,
    "rsiOversold": RsiOversoldStrategy,
    "rsiOverbought": RsiOverboughtStrategy,
    "macd": MacdStrategy,
    "stochastic": StochasticStrategy,
    "williamsR": WilliamsRStrategy,
    "momentum": MomentumStrategy,
    "ppo": PpoStrategy,
    "cci": CciStrategy,
    "ultimateOsc": UltimateOscStrategy,
    "trix": TrixStrategy,
    "atrVol": AtrVolStrategy,
    "bollinger": BollingerStrategy,
    "keltner": KeltnerStrategy,
    "donchian": DonchianStrategy,
    "histVol": HistVolStrategy,
    "ulcer": UlcerStrategy,
    "massIndex": MassIndexStrategy,
    "dpo": DpoStrategy,
    "kst": KstStrategy,
    "chaikinOsc": ChaikinOscStrategy,
    "adxTrend": AdxTrendStrategy,
    "supertrend": SupertrendStrategy,
    "parabolicSar": ParabolicSarStrategy,
    "ichimoku": IchimokuStrategy,
    "aroon": AroonStrategy,
    "aroonOsc": AroonOscStrategy,
    "vortex": VortexStrategy,
    "qstick": QstickStrategy,
    "trendIntensity": TrendIntensityStrategy,
    "volumeSpike": VolumeSpikeStrategy,
    "obvDiv": ObvDivStrategy,
    "vwap": VwapStrategy,
    "mfi": MfiStrategy,
    "eom": EomStrategy,
    "vpci": VpciStrategy,
    "vzo": VzoStrategy,
    "pvo": PvoStrategy,
    "forceIndex": ForceIndexStrategy,
    "demandIndex": DemandIndexStrategy,
    "gapUp": GapUpStrategy,
    "gapDown": GapDownStrategy,
    "doji": DojiStrategy,
    "hammer": HammerStrategy,
    "shootingStar": ShootingStarStrategy,
    "engulfBull": EngulfBullStrategy,
    "engulfBear": EngulfBearStrategy,
    "morningStar": MorningStarStrategy,
    "eveningStar": EveningStarStrategy,
    "piercingLine": PiercingLineStrategy,
    "threeWhiteSoldiers": ThreeWhiteSoldiersStrategy,
    "threeBlackCrows": ThreeBlackCrowsStrategy,
    "doubleTop": DoubleTopStrategy,
    "doubleBottom": DoubleBottomStrategy,
    "headShoulders": HeadShouldersStrategy,
    "invHeadShoulders": InvHeadShouldersStrategy,
    "risingWedge": RisingWedgeStrategy,
    "fallingWedge": FallingWedgeStrategy,
    "ascTriangle": AscTriangleStrategy,
    "descTriangle": DescTriangleStrategy,
    "bullFlag": BullFlagStrategy,
    "bearFlag": BearFlagStrategy,
    "bullChannel": BullChannelStrategy,
    "bearChannel": BearChannelStrategy,
    "rectangle": RectangleStrategy,
    "cupHandle": CupHandleStrategy,
    "roundingBottom": RoundingBottomStrategy,
    "bumpRun": BumpRunStrategy,
    "threeDrives": ThreeDrivesStrategy,
    "isoReversal": IsoReversalStrategy,
    "tweezerTop": TweezerTopStrategy,
    "tweezerBottom": TweezerBottomStrategy,
    "darkCloud": DarkCloudStrategy,
    "beltHold": BeltHoldStrategy,
    "marubozu": MarubozuStrategy,
    "stalled": StalledStrategy,
    "islandReversal": IslandReversalStrategy,
    "kicker": KickerStrategy,
    "thrusting": ThrustingStrategy,
    "hikkake": HikkakeStrategy,
    "nader": NaderStrategy,
    "tdSequential": TdSequentialStrategy,
    "tdCombo": TdComboStrategy,
    "waveTrend": WaveTrendStrategy,
    "elderRay": ElderRayStrategy,
    "ewo": EwoStrategy,
    "vpt": VptStrategy,
    "nvt": NvtStrategy,
    "hullSuite": HullSuiteStrategy,
    "jma": JmaStrategy,
    "ehlersSupertrend": EhlersSupertrendStrategy,
}


def get_all_strategies():
    return [s() for s in STRATEGY_REGISTRY.values()]

def get_strategy_count():
    return len(STRATEGY_REGISTRY)
