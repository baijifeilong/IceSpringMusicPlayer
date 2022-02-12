# Created by BaiJiFeiLong@gmail.com at 2022/2/12 19:19
import collections
import logging
import math
import typing

import numpy as np
from PySide2 import QtWidgets, QtGui, QtCore
from scipy import signal

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class SpectrumWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("spectrumWidget")
        self._logger.setLevel(logging.INFO)
        self._player = App.instance().getPlayer()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._onTimeout)
        self._timer.start(40)

    def _onTimeout(self):
        self._logger.debug("On timeout, repaint")
        music = self._player.getCurrentMusic()
        if music.isPresent():
            samples = self._player.getSamples()
            reportedDuration = self._player.getDuration()
            realDuration = int(len(samples) / music.get().sampleRate * 1000)
            self._logger.debug("Report duration: %d, real duration: %d", reportedDuration, realDuration)
        self.repaint()

    def smoothArray(self, arr: typing.List[float]):
        up, down = 0.9, 0.9
        oldArr = getattr(self, "__arr", [])
        for i in range(len(oldArr)):
            if arr[i] < oldArr[i]:
                arr[i] = arr[i] * down + oldArr[i] * (1 - down)
            else:
                arr[i] = arr[i] * up + oldArr[i] * (1 - up)
        setattr(self, "__arr", arr)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        music = self._player.getCurrentMusic()
        samples = self._player.getSamples()
        if not music.isPresent():
            self._logger.debug("Music not present, skip")
            return
        if len(samples) == 0:
            self._logger.debug("No samples, skip")
            return
        sampleRate = music.get().sampleRate
        baseFrequency, maxFrequency, barCount, minDbfs, sampleCount = 50, 20000, 30, -60, 1500
        powerRoot = pow(maxFrequency / baseFrequency, 1 / barCount)
        sampleIndex = int(self._player.getPosition() / 1000 * sampleRate)
        segments = samples[sampleIndex:sampleIndex + sampleCount]
        frequencies, powers = signal.welch(segments, fs=sampleRate, nperseg=sampleCount, scaling="spectrum")
        powers[powers == 0] = 2 ** -40
        powers = np.log10(powers * 2) * 10
        spacing = self.width() // barCount
        valuesDict = collections.defaultdict(list)
        painter = QtGui.QPainter(self)
        for frequency, power in zip(frequencies, powers):
            valuesIndex = 0 if frequency == 0 else int(math.log(frequency / baseFrequency, powerRoot))
            valuesDict[min(max(0, valuesIndex), barCount - 1)].append(power)
        values = [-sum(x) / len(x) for x in valuesDict.values()]
        self.smoothArray(values)
        for valuesIndex, value in enumerate(values):
            unit = self.height() / -minDbfs
            painter.fillRect(valuesIndex * spacing, int(value * unit), spacing - 1, self.height(),
                QtGui.QColor("#4477CC"))
