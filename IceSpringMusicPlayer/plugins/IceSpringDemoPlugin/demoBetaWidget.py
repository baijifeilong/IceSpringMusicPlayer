# Created by BaiJiFeiLong@gmail.com at 2022/1/21 16:11
from IceSpringRealOptional.typingUtils import unused, gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class DemoBetaWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self, parent, config):
        super().__init__(parent)
        unused(config)
        self.setLayout(QtWidgets.QGridLayout(self))
        label = QtWidgets.QLabel("This is DemoBetaWidget", self)
        label.setAlignment(gg(QtCore.Qt.AlignmentFlag.AlignCenter))
        self.layout().addWidget(label)
