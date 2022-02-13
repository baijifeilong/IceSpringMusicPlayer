# Created by BaiJiFeiLong@gmail.com at 2022/2/13 20:54
import dataclasses

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class SpectrumWidgetConfig(JsonSupport):
    barCount: int
    distribution: str
    baseFrequency: int
    minFrequency: int
    maxFrequency: int
    smoothUp: float
    smoothDown: float

    @classmethod
    def getDefaultObject(cls) -> JsonSupport:
        return cls(barCount=100, distribution="EXPONENTIAL", baseFrequency=50, minFrequency=0, maxFrequency=22000,
            smoothUp=0.9, smoothDown=0.7)
