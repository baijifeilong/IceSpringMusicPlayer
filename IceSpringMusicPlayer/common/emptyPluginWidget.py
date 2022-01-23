# Created by BaiJiFeiLong@gmail.com at 2022/1/21 14:06
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class EmptyPluginWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self):
        super().__init__()
        label = QtWidgets.QLabel("Empty", self)
        label.setAlignment(gg(QtCore.Qt.AlignmentFlag.AlignCenter))
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(label)
