# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:00
import typing

from PySide2 import QtWidgets

from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class FinalMeta(type(QtWidgets.QWidget), type(PluginMixin)):
    pass


class DemoWidget(QtWidgets.QWidget, PluginMixin, ReplaceableMixin, metaclass=FinalMeta):
    @classmethod
    def id(cls) -> str:
        return "IceSpringDemoPlugin"

    @classmethod
    def name(cls) -> Text:
        text = Text()
        text.en_US = "Demo Plugin"
        return text

    @classmethod
    def replaceableWidgets(cls) -> typing.Dict[Text, typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]]:
        return {
            cls.name(): lambda parent: cls(parent)
        }

    def __init__(self, parent):
        super().__init__(parent)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(QtWidgets.QLabel("OK", self))
