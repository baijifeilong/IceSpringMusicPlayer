# Created by BaiJiFeiLong@gmail.com at 2022/1/21 17:13
import typing

from IceSpringRealOptional.typingUtils import unused, gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class HelloWorldPlugin(PluginMixin):
    @classmethod
    def getWidgetClasses(cls) -> typing.List[typing.Type[PluginWidgetMixin]]:
        return [HelloWorldWidget]


class HelloWorldWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self, parent, config):
        super().__init__(parent)
        unused(config)
        label = QtWidgets.QLabel("Hello World", self)
        label.setAlignment(gg(QtCore.Qt.AlignmentFlag.AlignCenter))
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(label)
