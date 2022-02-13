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
        self._barCountComboBox = QtWidgets.QComboBox()
        self._barCountComboBox.addItems(list(map(str, range(10, 210, 10))))
        self._barCountComboBox.setCurrentText(str(self._widgetConfig.barCount))
        self._distributionComboBox = QtWidgets.QComboBox()
        self._distributionComboBox.addItem(tt.spectrumWidget_frequencyDistributionExponential)
        self._distributionComboBox.addItem(tt.spectrumWidget_frequencyDistributionLinear)
        self._distributionComboBox.setCurrentIndex(["EXPONENTIAL", "LINEAR"].index(self._widgetConfig.distribution))
        self._buttonBox = WidgetUtils.createButtonBox(ok=True, cancel=True, apply=True)
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 2)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_barCount))
        mainLayout.addWidget(self._barCountComboBox)
        mainLayout.addWidget(QtWidgets.QLabel(tt.spectrumWidget_frequencyDistribution))
        mainLayout.addWidget(self._distributionComboBox)
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
            self._target.widgetConfigChanged.emit()
        if role in [QtWidgets.QDialogButtonBox.AcceptRole, QtWidgets.QDialogButtonBox.RejectRole]:
            self.close()
