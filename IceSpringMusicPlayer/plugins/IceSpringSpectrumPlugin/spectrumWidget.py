# Created by BaiJiFeiLong@gmail.com at 2022/2/12 19:19
import logging
import math
import random
import statistics
import typing

import numpy as np
from IceSpringRealOptional.just import Just
from PySide2 import QtWidgets, QtGui, QtCore
from assertpy import assert_that
from scipy import signal

import IceSpringSpectrumPlugin.spectrumTranslation as tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.utils.layoutUtils import LayoutUtils
from IceSpringSpectrumPlugin.spectrumWidgetConfig import SpectrumWidgetConfig


class SpectrumWidget(QtWidgets.QWidget, PluginWidgetMixin):
    widgetConfigChanged: QtCore.SignalInstance = QtCore.Signal()
    _widgetConfig: SpectrumWidgetConfig
    _barCount: int
    _distribution: str
    _baseFrequency: int
    _minFrequency: int
    _maxFrequency: int
    _smoothUp: float
    _smoothDown: float
    _spacing: int
    _margins: typing.List[int]
    _drawDbfsNumbers: bool
    _drawDbfsLines: bool
    _drawFrequencyLabels: bool
    _overlayDbfsNumbers: bool
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
        self._app = App.instance()
        self._updateRate = 20
        self._refreshRate = 60
        self._sampleMillis = 33
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
        self.setPalette(Just.of(self.palette()).apply(
            lambda x: x.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("white"))).value())

    def _onCustomContextMenuRequested(self) -> None:
        from IceSpringSpectrumPlugin.spectrumWidgetConfigDialog import SpectrumWidgetConfigDialog
        self._logger.info("On custom context menu requested")
        menu = QtWidgets.QMenu(self)
        menu.addAction(tt.Plugins_ConfigWidget, lambda: SpectrumWidgetConfigDialog(self).exec_())
        menu.addAction(tt.Plugins_ToggleFullscreen, lambda: LayoutUtils.toggleFullscreen(self))
        menu.exec_(QtGui.QCursor.pos())

    def _onWidgetConfigChanged(self):
        self._logger.info("On widget config changed")
        self._loadConfig()

    # noinspection DuplicatedCode
    def _loadConfig(self):
        self._logger.info("Load config")
        self._barCount = self._widgetConfig.barCount
        self._distribution = self._widgetConfig.distribution
        self._minFrequency = self._widgetConfig.minFrequency
        self._maxFrequency = self._widgetConfig.maxFrequency
        self._baseFrequency = self._widgetConfig.baseFrequency
        self._smoothUp = self._widgetConfig.smoothUp
        self._smoothDown = self._widgetConfig.smoothDown
        self._minDbfs = self._widgetConfig.minDbfs
        self._spacing = self._widgetConfig.spacing
        self._margins = self._widgetConfig.margins
        self._drawDbfsNumbers = self._widgetConfig.drawDbfsNumbers
        self._drawDbfsLines = self._widgetConfig.drawDbfsLines
        self._drawFrequencyLabels = self._widgetConfig.drawFrequencyLabels
        self._overlayDbfsNumbers = self._widgetConfig.overlayDbfsNumbers
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
        spacing, barCount, minDbfs = self._spacing, self._barCount, self._minDbfs
        marginTop, marginRight, marginBottom, marginLeft = self._margins
        drawDbfsNumbers, drawDbfsLines, drawFrequencyLabels, overlayDbfsNumbers = \
            self._drawDbfsNumbers, self._drawDbfsLines, self._drawFrequencyLabels, self._overlayDbfsNumbers
        fontSize = self.font().pointSize()
        labelHeight = fontSize * 2 if drawFrequencyLabels else 0
        dbfsWidth = fontSize * 6 if drawDbfsNumbers else 0
        tailWidth = 0 if overlayDbfsNumbers else dbfsWidth
        thresholds, smooths = self._thresholds, self._smooths
        rect = QtCore.QRect(QtCore.QPoint(marginLeft, marginTop),
            QtCore.QPoint(self.width() - marginRight - 1, self.height() - marginBottom - 1))
        unitHeight = max((rect.height() - labelHeight) / (-minDbfs + 5), 0)
        headerHeight = int(unitHeight * 5)
        painter = QtGui.QPainter(self)
        prevDbfsY = rect.top() + headerHeight - 0.5 * fontSize
        for dbfs in range(0, minDbfs - 1, -10):
            y = int(-dbfs * unitHeight + headerHeight)
            if drawDbfsLines:
                painter.setPen(QtGui.QColor("#CCCCCC"))
                painter.drawLine(rect.left(), rect.top() + y, rect.right() - dbfsWidth, rect.top() + y)
            if drawDbfsNumbers:
                painter.setPen(QtGui.QColor("#000000"))
                dbfsY = rect.top() + y + fontSize // 2
                if dbfsY - prevDbfsY >= fontSize * 1.5:
                    painter.drawText(rect.right() - dbfsWidth + fontSize // 2, dbfsY, f"{dbfs: 3}db")
                    prevDbfsY = dbfsY
        prevLabelX, prevBarX = -10000, -10000
        span: float = (rect.width() - tailWidth) / barCount
        painter.setPen(QtGui.QColor("#000000"))
        for i, (k, v) in enumerate(zip(thresholds, smooths)):
            v = max(v, minDbfs)
            x, y = int(i * span), math.ceil(-v * unitHeight + headerHeight)
            w, h = max(int(span - spacing), 1), max(rect.height() - y - labelHeight, 0)
            if x - prevBarX > spacing:
                painter.fillRect(rect.left() + x, rect.top() + y, w, h, QtGui.QColor("#4477CC"))
                prevBarX = x
            hz = str(k) if k < 1000 else ("%.1fK" if k < 10000 else "%.0fK") % (k / 1000)
            lx, ly = int(x + span / 2 - len(hz) * fontSize / 2), rect.height() - 3
            if 0 <= lx < rect.right() - len(hz) * fontSize * 1.7 and lx - prevLabelX >= (len(hz) + 2) * fontSize \
                    and drawFrequencyLabels:
                painter.drawText(rect.left() + lx, rect.top() + ly, hz)
                prevLabelX = lx

    @staticmethod
    def calcPowerValues(frequencies, powers, thresholds, minFrequency):
        powers[powers == 0] = 10 ** -20
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
                value = -120
            values.append(value)
        validIndexes = [i for i, v in enumerate(values) if v != -120]
        if len(validIndexes) > 0:
            for index in range(0, validIndexes[-1], 1):
                if values[index] == -120:
                    samples = [x for x in values[max(index - 2, 0):index + 3] if x != -120] or [
                        x for x in values if x != -120]
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
