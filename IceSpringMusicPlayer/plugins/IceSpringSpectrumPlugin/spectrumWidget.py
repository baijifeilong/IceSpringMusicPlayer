# Created by BaiJiFeiLong@gmail.com at 2022/2/12 19:19
import logging
import random
import statistics
import typing

import numpy as np
from PySide2 import QtWidgets, QtGui, QtCore
from scipy import signal

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class SpectrumWidget(QtWidgets.QWidget, PluginWidgetMixin):
    _thresholds: typing.List[int]
    _values: typing.List[float]
    _smooths: typing.List[float]

    def __init__(self):
        super().__init__()
        self._minDbfs = -60
        self._minFrequency = 50
        self._maxFrequency = 22000
        self._barCount = 100
        self._updateRate = 20
        self._refreshRate = 60
        self._sampleMillis = 33
        self._smoothUp = 0.9
        self._smoothDown = 0.9
        self._logger = logging.getLogger("spectrumWidget")
        self._logger.setLevel(logging.INFO)
        self._player = App.instance().getPlayer()
        self._thresholds = []
        self._values = []
        self._smooths = []
        self._doInit()
        self._updateTimer = QtCore.QTimer(self)
        self._updateTimer.timeout.connect(self._doUpdateSpectrum)
        self._updateTimer.start(1000 // self._updateRate)
        self._repaintTimer = QtCore.QTimer(self)
        self._repaintTimer.timeout.connect(self._doSmooth)
        self._repaintTimer.timeout.connect(self.repaint)
        self._repaintTimer.start(1000 // self._refreshRate)

    def _doInit(self):
        powerRoot = pow(self._maxFrequency / self._minFrequency, 1 / (self._barCount - 1))
        self._thresholds = [round(self._minFrequency * pow(powerRoot, x)) for x in range(self._barCount)]

    def _doUpdateSpectrum(self):
        self._logger.debug("Do update spectrum")
        if not self._player.getCurrentMusic().isPresent():
            self._logger.debug("Music not present, skip")
            return
        if len(self._player.getSamples()) == 0:
            self._logger.debug("No samples, skip")
            return
        music = self._player.getCurrentMusic().get()
        samples = self._player.getSamples()
        sampleRate = music.sampleRate
        sampleCount = int(self._sampleMillis / 1000 * sampleRate)
        sampleIndex = int(self._player.getPosition() / 1000 * sampleRate)
        segments = samples[sampleIndex:sampleIndex + sampleCount]
        frequencies, powers = signal.welch(segments, fs=sampleRate, nperseg=sampleCount, scaling="spectrum")
        self._values = self.calcPowerValues(frequencies, powers, self._thresholds)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        spacing = self.width() // self._barCount
        painter = QtGui.QPainter(self)
        for i, (k, v) in enumerate(zip(self._thresholds, self._smooths)):
            unit = self.height() / -self._minDbfs
            painter.fillRect(i * spacing, int(-v * unit), spacing - 1, self.height(), QtGui.QColor("#4477CC"))

    @staticmethod
    def calcPowerValues(frequencies, powers, thresholds):
        powers[powers == 0] = 2 ** -40
        powers = np.log10(powers * 2) * 10
        prevThresholds = [0] + thresholds[:-1]
        powerArrays = [[] for _ in range(len(thresholds))]
        for frequency, power in zip(frequencies, powers):
            for index, (prevThreshold, threshold) in enumerate(zip(prevThresholds, thresholds)):
                if prevThreshold <= frequency < threshold:
                    powerArrays[index].append(power)
        values = []
        for index, powerArray in enumerate(powerArrays):
            if len(powerArray) > 0:
                value = statistics.mean(powerArray)
            elif index == 0:
                value = -90
            else:
                value = statistics.mean(values[-3:]) * ((random.random() - 0.5) * 2 * 0.2 + 1)
            values.append(value)
        return values

    def _doSmooth(self):
        up, down = self._smoothUp, self._smoothDown
        if len(self._smooths) != len(self._values):
            self._smooths = self._values[:]
        for i in range(len(self._values)):
            if self._values[i] < self._smooths[i]:
                self._smooths[i] = self._values[i] * down + self._smooths[i] * (1 - down)
            else:
                self._smooths[i] = self._values[i] * up + self._smooths[i] * (1 - up)
