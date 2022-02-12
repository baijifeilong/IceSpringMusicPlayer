# Created by BaiJiFeiLong@gmail.com at 2022/2/12 19:22

import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


spectrumPlugin_Name = Text()
spectrumPlugin_Name.en_US = "Spectrum Plugin"
spectrumPlugin_Name.zh_CN = "频谱图插件"
spectrumWidget_Name = Text()
spectrumWidget_Name.en_US = "Spectrum Widget"
spectrumWidget_Name.zh_CN = "频谱图组件"
