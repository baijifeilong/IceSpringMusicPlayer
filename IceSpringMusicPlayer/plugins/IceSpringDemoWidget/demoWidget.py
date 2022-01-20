# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:00
import typing

from PySide2 import QtWidgets

from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class DemoWidget(QtWidgets.QWidget, PluginMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(QtWidgets.QLabel("OK", self))

    @classmethod
    def replaceableWidgets(cls: typing.Type[typing.Union[PluginMixin, QtWidgets.QWidget]]) \
            -> typing.Dict[Text, typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]]:
        from IceSpringDemoWidget.demoConfigWidget import DemoConfigWidget
        return {
            **super().replaceableWidgets(),
            Text.of(en_US="DemoConfigWidget", zh_CN="玳瑁"): lambda parent: DemoConfigWidget(parent)
        }
