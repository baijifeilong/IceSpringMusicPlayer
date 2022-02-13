# Created by BaiJiFeiLong@gmail.com at 2022/2/12 19:19
import logging
import random
import statistics
import typing

import numpy as np
from PySide2 import QtWidgets, QtGui, QtCore
from assertpy import assert_that
from scipy import signal

import IceSpringSpectrumPlugin.spectrumTranslation as tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringSpectrumPlugin.spectrumWidgetConfig import SpectrumWidgetConfig


class SpectrumWidget(QtWidgets.QWidget, PluginWidgetMixin):
    widgetConfigChanged: QtCore.SignalInstance = QtCore.Signal()
    _widgetConfig: SpectrumWidgetConfig
    _barCount: int
    _distribution: str
    _baseFrequency: int
    _minFrequency: int
    _maxFrequency: int
    _thresholds: typing.List[int]
    _values: typing.List[float]
    _smooths: typing.List[float]

    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[JsonSupport]:
        return SpectrumWidgetConfig

    def getWidgetConfig(self) -> SpectrumWidgetConfig:
        return self._widgetConfig

    def __init__(self, config=None):
        super().__init__()
        self._widgetConfig = config or self.getWidgetConfigClass().getDefaultObject()
        self._minDbfs = -60
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
        self._loadConfig()
        self._updateTimer = QtCore.QTimer(self)
        self._updateTimer.timeout.connect(self._doUpdateSpectrum)
        self._updateTimer.start(1000 // self._updateRate)
        self._repaintTimer = QtCore.QTimer(self)
        self._repaintTimer.timeout.connect(self._doSmooth)
        self._repaintTimer.timeout.connect(self.repaint)
        self._repaintTimer.start(1000 // self._refreshRate)
        self.setFont(QtGui.QFont("", 10))
        self.widgetConfigChanged.connect(self._onWidgetConfigChanged)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCustomContextMenuRequested)

    def _onCustomContextMenuRequested(self) -> None:
        from IceSpringSpectrumPlugin.spectrumWidgetConfigDialog import SpectrumWidgetConfigDialog
        self._logger.info("On custom context menu requested")
        menu = QtWidgets.QMenu(self)
        menu.addAction(tt.Plugins_ConfigWidget, lambda: SpectrumWidgetConfigDialog(self).exec_())
        menu.exec_(QtGui.QCursor.pos())

    def _onWidgetConfigChanged(self):
        self._logger.info("On widget config changed")
        self._loadConfig()

    def _loadConfig(self):
        self._logger.info("Load config")
        self._barCount = self._widgetConfig.barCount
        self._distribution = self._widgetConfig.distribution
        self._minFrequency = self._widgetConfig.minFrequency
        self._maxFrequency = self._widgetConfig.maxFrequency
        self._baseFrequency = self._widgetConfig.baseFrequency
        assert_that(self._distribution).is_in("EXPONENTIAL", "LINEAR")
        if self._distribution == "EXPONENTIAL":
            powerRoot = pow(self._maxFrequency / self._baseFrequency, 1 / (self._barCount - 1))
            self._thresholds = [round(self._baseFrequency * pow(powerRoot, x)) for x in range(self._barCount)]
        else:
            step = (self._maxFrequency - self._minFrequency) / self._barCount
            self._thresholds = [round((x + 1) * step + self._minFrequency) for x in range(self._barCount)]
        self._thresholds = [x for x in self._thresholds if x >= self._minFrequency]

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
        self._values = self.calcPowerValues(frequencies, powers, self._thresholds, self._minFrequency)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        padRight, padBottom, padLeft = 0, 20, 0
        spacing = (self.width() - padLeft - padRight) // self._barCount
        unitHeight = (self.height() - padBottom) / (-self._minDbfs + 5)
        padTop = int(unitHeight * 5)
        painter = QtGui.QPainter(self)
        for dbfs in range(0, self._minDbfs - 1, -10):
            y = int(-dbfs * unitHeight + padTop)
            painter.setPen(QtGui.QColor("#CCCCCC"))
            painter.drawLine(0, y, self.width() - 50, y)
            painter.setPen(QtGui.QColor("#000000"))
            painter.drawText(self.width() - 45, y + 5, f"{dbfs: 3}db")
        prevLabel = -1
        for i, (k, v) in enumerate(zip(self._thresholds, self._smooths)):
            v = max(v, self._minDbfs)
            x, y = i * spacing + padLeft, round(-v * unitHeight) + padTop
            w, h = spacing - 1, self.height() - y - padBottom
            painter.fillRect(x, y, w, h, QtGui.QColor("#4477CC"))
            hz = str(k) if k < 1000 else ("%.1fK" if k < 10000 else "%.0fK") % (k / 1000)
            if (i - prevLabel) * spacing > 40:
                painter.drawText(x + spacing // 2 - 4 * len(hz), self.height() - 3, hz)
                prevLabel = i

    @staticmethod
    def calcPowerValues(frequencies, powers, thresholds, minFrequency):
        powers[powers == 0] = 2 ** -40
        powers = np.log10(powers * 2) * 10
        prevThresholds = [minFrequency] + thresholds[:-1]
        powerArrays = [[] for _ in range(len(thresholds))]
        for frequency, power in zip(frequencies, powers):
            for index, (prevThreshold, threshold) in enumerate(zip(prevThresholds, thresholds)):
                if prevThreshold <= frequency < threshold:
                    powerArrays[index].append(power)
        values = []
        for index, powerArray in enumerate(powerArrays):
            if len(powerArray) > 0:
                value = statistics.mean(powerArray)
            else:
                value = -90
            values.append(value)
        validIndexes = [i for i, v in enumerate(values) if v != -90]
        if len(validIndexes) > 0:
            for index in range(0, validIndexes[-1], 1):
                if values[index] == -90:
                    samples = [x for x in values[max(index - 2, 0):index + 3] if x != -90] or [
                        x for x in values if x != 90]
                    values[index] = statistics.mean(samples) * ((random.random() - 0.5) * 2 * 0.2 + 1)
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
