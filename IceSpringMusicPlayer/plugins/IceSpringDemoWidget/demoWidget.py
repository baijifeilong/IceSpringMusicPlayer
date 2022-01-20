# Created by BaiJiFeiLong@gmail.com at 2022/1/20 10:00
import logging
import typing

from PySide2 import QtWidgets, QtCore

from IceSpringDemoWidget.demoGlobalConfig import DemoGlobalConfig
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class DemoWidget(QtWidgets.QWidget, PluginMixin):
    globalConfigChanged: QtCore.SignalInstance = QtCore.Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self._logger = logging.getLogger("demoWidget")
        self._globalConfig = self.getGlobalConfig()
        self._button = QtWidgets.QPushButton(self._globalConfig.prefix, self)
        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().addWidget(self._button)
        self._button.clicked.connect(self._onButtonClicked)
        self.globalConfigChanged.connect(self._onGlobalConfigChanged)

    def _onButtonClicked(self) -> None:
        self._logger.info("On button clicked")
        self._globalConfig.prefix = "Prefix" + str(int(self._globalConfig.prefix[len("Prefix"):]) + 1)
        self._logger.info("> Signal globalConfigChanged emitting...")
        self.globalConfigChanged.emit()
        self._logger.info("< Signal globalConfigChanged emitted.")

    def _onGlobalConfigChanged(self) -> None:
        self._logger.info("On global config changed")
        self._button.setText(self._globalConfig.prefix)

    @classmethod
    def replaceableWidgets(cls: typing.Type[typing.Union[PluginMixin, QtWidgets.QWidget]]) \
            -> typing.Dict[Text, typing.Callable[[QtWidgets.QWidget], ReplaceableMixin]]:
        from IceSpringDemoWidget.demoConfigWidget import DemoConfigWidget
        return {
            **super().replaceableWidgets(),
            Text.of(en_US="DemoConfigWidget"): lambda parent: DemoConfigWidget(parent)
        }

    @classmethod
    def configFromJson(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]) -> typing.Any:
        jd = dict(pairs)
        if jd.get("id", None) == ".".join((cls.__module__, cls.__name__)):
            return DemoGlobalConfig(**jd)
        return dict(**jd)

    @classmethod
    def configToJson(cls, obj: typing.Any) -> typing.Any:
        if isinstance(obj, type):
            return ".".join((obj.__module__, obj.__name__))
        return obj.__dict__

    @classmethod
    def getDefaultConfig(cls) -> DemoGlobalConfig:
        return DemoGlobalConfig(
            id=".".join((cls.__module__, cls.__name__)),
            prefix="Prefix1"
        )

    @classmethod
    def getGlobalConfig(cls) -> DemoGlobalConfig:
        return super().getGlobalConfig()
