# Created by BaiJiFeiLong@gmail.com at 2022/1/22 15:31
import types
import typing

from PySide2 import QtWidgets

import IceSpringPluginManagerPlugin.pluginManagerTranslation as tt
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.utils.dialogUtils import DialogUtils


class PluginManagerPlugin(PluginMixin):
    @classmethod
    def getPluginName(cls) -> Text:
        return tt.PluginManagerPlugin_Name

    @classmethod
    def getPluginTranslationModule(cls) -> types.ModuleType:
        return tt

    @classmethod
    def getPluginMenus(cls) -> typing.List[typing.Union[QtWidgets.QAction, QtWidgets.QMenu]]:
        from IceSpringPluginManagerPlugin.pluginManagerWidget import PluginManagerWidget
        action = QtWidgets.QAction(tt.PluginsMenu_ConfigPlugin)
        action.triggered.connect(lambda: DialogUtils.execWidget(PluginManagerWidget(), withOk=True))
        return [action]

    @classmethod
    def isSystemPlugin(cls) -> bool:
        return True
