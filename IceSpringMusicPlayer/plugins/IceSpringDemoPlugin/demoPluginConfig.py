# Created by BaiJiFeiLong@gmail.com at 2022/1/20 13:41
import dataclasses

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class DemoPluginConfig(JsonSupport):
    pluginCounter: int

    @classmethod
    def getDefaultObject(cls) -> JsonSupport:
        return DemoPluginConfig(pluginCounter=0)
