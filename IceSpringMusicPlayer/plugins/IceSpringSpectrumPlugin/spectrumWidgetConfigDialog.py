# Created by BaiJiFeiLong@gmail.com at 2022/2/13 21:03

import logging

from PySide2 import QtWidgets

import IceSpringSpectrumPlugin.spectrumTranslation as tt
from IceSpringMusicPlayer.utils.widgetUtils import WidgetUtils
from IceSpringSpectrumPlugin.spectrumWidget import SpectrumWidget


class SpectrumWidgetConfigDialog(QtWidgets.QDialog):
    def __init__(self, target: SpectrumWidget):
        super().__init__(QtWidgets.QApplication.activeWindow())
        self._target = target
        self._logger = logging.getLogger("spectrumWidgetConfig")
        self._widgetConfig = self._target.getWidgetConfig()
        barCounts = [*range(1, 10, 1), *range(10, 100, 10), *range(100, 1001, 100)]
        self._barCountComboBox = QtWidgets.QComboBox()
        self._barCountComboBox.addItems(list(map(str, barCounts)))
        self._barCountComboBox.setCurrentText(str(self._widgetConfig.barCount))
        self._distributionComboBox = QtWidgets.QComboBox()
        self._distributionComboBox.addItem(tt.spectrumWidget_frequencyDistributionExponential)
        self._distributionComboBox.addItem(tt.spectrumWidget_frequencyDistributionLinear)
        self._distributionComboBox.setCurrentIndex(["EXPONENTIAL", "LINEAR"].index(self._widgetConfig.distribution))
        frequencies = [*range(10, 100, 10), *range(100, 1000, 100), *range(1000, 30001, 1000)]
        self._baseFrequencyComboBox = QtWidgets.QComboBox()
        self._baseFrequencyComboBox.addItems(list(map(str, frequencies)))
        self._baseFrequencyComboBox.setCurrentText(str(self._widgetConfig.baseFrequency))
        self._minFrequencyComboBox = QtWidgets.QComboBox()
        self._minFrequencyComboBox.addItems(list(map(str, [0] + frequencies)))
        self._minFrequencyComboBox.setCurrentText(str(self._widgetConfig.minFrequency))
        self._maxFrequencyComboBox = QtWidgets.QComboBox()
        self._maxFrequencyComboBox.addItems(list(map(str, frequencies)))
        self._maxFrequencyComboBox.setCurrentText(str(self._widgetConfig.maxFrequency))
        self._smoothUpComboBox = QtWidgets.QComboBox()
        self._smoothUpComboBox.addItems(list(map(str, reversed(range(1, 101)))))
        self._smoothUpComboBox.setCurrentText(str(round(self._widgetConfig.smoothUp * 100)))
        self._smoothDownComboBox = QtWidgets.QComboBox()
        self._smoothDownComboBox.addItems(list(map(str, reversed(range(1, 101)))))
        self._smoothDownComboBox.setCurrentText(str(round(self._widgetConfig.smoothDown * 100)))
        self._minDbfsComboBox = QtWidgets.QComboBox()
        self._minDbfsComboBox.addItems(list(map(str, range(-120, 0, 1))))
        self._minDbfsComboBox.setCurrentText(str(self._widgetConfig.minDbfs))
        spacings = [*range(1, 10, 1), *range(10, 101, 10)]
        self._spacingComboBox = QtWidgets.QComboBox()
        self._spacingComboBox.addItems(list(map(str, spacings)))
        self._spacingComboBox.setCurrentText(str(self._widgetConfig.spacing))
        self._buttonBox = WidgetUtils.createButtonBox(ok=True, cancel=True, apply=True)
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 2)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_barCount))
        mainLayout.addWidget(self._barCountComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_frequencyDistribution))
        mainLayout.addWidget(self._distributionComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_baseFrequency))
        mainLayout.addWidget(self._baseFrequencyComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_minFrequency))
        mainLayout.addWidget(self._minFrequencyComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_maxFrequency))
        mainLayout.addWidget(self._maxFrequencyComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_smoothUp))
        mainLayout.addWidget(self._smoothUpComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_smoothDown))
        mainLayout.addWidget(self._smoothDownComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_minDbfs))
        mainLayout.addWidget(self._minDbfsComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_spacing))
        mainLayout.addWidget(self._spacingComboBox)
        mainLayout.addWidget(WidgetUtils.createExpandingSpacer(), mainLayout.rowCount(), 0, 1, 2)
        mainLayout.addWidget(self._buttonBox, mainLayout.rowCount(), 0, 1, 2)
        self.setLayout(mainLayout)
        self.resize(854, 480)
        self._buttonBox.clicked.connect(self._onButtonBoxClicked)

    def _onButtonBoxClicked(self, button: QtWidgets.QPushButton) -> None:
        self._logger.info("On button box clicked")
        role = self._buttonBox.buttonRole(button)
        if role in [QtWidgets.QDialogButtonBox.ApplyRole, QtWidgets.QDialogButtonBox.AcceptRole]:
            self._widgetConfig.barCount = int(self._barCountComboBox.currentText())
            self._widgetConfig.distribution = ["EXPONENTIAL", "LINEAR"][self._distributionComboBox.currentIndex()]
            self._widgetConfig.baseFrequency = int(self._baseFrequencyComboBox.currentText())
            self._widgetConfig.minFrequency = int(self._minFrequencyComboBox.currentText())
            self._widgetConfig.maxFrequency = int(self._maxFrequencyComboBox.currentText())
            self._widgetConfig.smoothUp = float(self._smoothUpComboBox.currentText()) / 100
            self._widgetConfig.smoothDown = float(self._smoothDownComboBox.currentText()) / 100
            self._widgetConfig.minDbfs = int(self._minDbfsComboBox.currentText())
            self._widgetConfig.spacing = int(self._spacingComboBox.currentText())
            self._target.widgetConfigChanged.emit()
        if role in [QtWidgets.QDialogButtonBox.AcceptRole, QtWidgets.QDialogButtonBox.RejectRole]:
            self.close()
