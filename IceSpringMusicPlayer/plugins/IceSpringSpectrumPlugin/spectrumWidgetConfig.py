# Created by BaiJiFeiLong@gmail.com at 2022/2/13 20:54
import dataclasses

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class SpectrumWidgetConfig(JsonSupport):
    barCount: int

    @classmethod
    def getDefaultObject(cls) -> JsonSupport:
        return cls(barCount=100)
