# Created by BaiJiFeiLong@gmail.com at 2022/2/12 19:18
import types
import typing

import IceSpringSpectrumPlugin.spectrumTranslation as tt
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text


class SpectrumPlugin(PluginMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.spectrumPlugin_Name

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        from IceSpringSpectrumPlugin.spectrumWidget import SpectrumWidget
        return {
            tt.spectrumPlugin_Name: lambda: SpectrumWidget()
        }

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt

    @classmethod
    def isSystemPlugin(cls) -> bool:
        return True
