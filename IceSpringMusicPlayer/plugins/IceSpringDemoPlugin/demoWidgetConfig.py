# Created by BaiJiFeiLong@gmail.com at 2022/1/20 15:31
import dataclasses

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class DemoWidgetConfig(JsonSupport):
    widgetCounter: int

    @classmethod
    def getDefaultObject(cls) -> JsonSupport:
        return DemoWidgetConfig(widgetCounter=0)
