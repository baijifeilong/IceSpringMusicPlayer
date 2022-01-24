# Created by BaiJiFeiLong@gmail.com at 2022/1/21 17:13

import typing

from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin
from IceSpringMusicPlayer.tt import Text


class HelloWorldPlugin(QtWidgets.QWidget, PluginMixin, PluginWidgetMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.HelloWorldPlugin_Name

    @classmethod
    def getPluginReplacers(cls) -> typing.Dict[Text, typing.Callable[[], PluginWidgetMixin]]:
        return {tt.HelloWorldWidget_Name: lambda: cls()}

    def __init__(self):
        super().__init__()
        label = QtWidgets.QLabel("Hello World", self)
        label.setAlignment(gg(QtCore.Qt.AlignmentFlag.AlignCenter))
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(label)
