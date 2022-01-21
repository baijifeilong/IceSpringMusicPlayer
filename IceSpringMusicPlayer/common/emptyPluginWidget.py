# Created by BaiJiFeiLong@gmail.com at 2022/1/21 14:06
from IceSpringRealOptional.typingUtils import unused, gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class EmptyPluginWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self, parent, config):
        super().__init__(parent)
        unused(config)
        label = QtWidgets.QLabel("Empty", self)
        label.setAlignment(gg(QtCore.Qt.AlignmentFlag.AlignCenter))
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(label)
