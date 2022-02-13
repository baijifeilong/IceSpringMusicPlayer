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
spectrumWidget_barCount = Text()
spectrumWidget_barCount.en_US = "Bar Count"
spectrumWidget_barCount.zh_CN = "频谱数量"
spectrumWidget_frequencyDistribution = Text()
spectrumWidget_frequencyDistribution.en_US = "Frequency Distribution"
spectrumWidget_frequencyDistribution.zh_CN = "频率分布"
spectrumWidget_frequencyDistributionExponential = Text()
spectrumWidget_frequencyDistributionExponential.en_US = "Exponential Distribution"
spectrumWidget_frequencyDistributionExponential.zh_CN = "指数分布"
spectrumWidget_frequencyDistributionLinear = Text()
spectrumWidget_frequencyDistributionLinear.en_US = "Linear Distribution"
spectrumWidget_frequencyDistributionLinear.zh_CN = "线性分布"
spectrumWidget_baseFrequency = Text()
spectrumWidget_baseFrequency.en_US = "Exponential Base Frequency"
spectrumWidget_baseFrequency.zh_CN = "指数分布基准频率"
spectrumWidget_minFrequency = Text()
spectrumWidget_minFrequency.en_US = "Min Frequency"
spectrumWidget_minFrequency.zh_CN = "最低频率"
spectrumWidget_maxFrequency = Text()
spectrumWidget_maxFrequency.en_US = "Max Frequency"
spectrumWidget_maxFrequency.zh_CN = "最高频率"
spectrumWidget_smoothUp = Text()
spectrumWidget_smoothUp.en_US = "Smooth Up Factor"
spectrumWidget_smoothUp.zh_CN = "平滑上升因子"
spectrumWidget_smoothDown = Text()
spectrumWidget_smoothDown.en_US = "Smooth Down Factor"
spectrumWidget_smoothDown.zh_CN = "平滑下降因子"
