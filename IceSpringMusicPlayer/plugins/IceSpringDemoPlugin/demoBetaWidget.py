# Created by BaiJiFeiLong@gmail.com at 2022/1/21 16:11
from IceSpringRealOptional.typingUtils import gg
from PySide2 import QtWidgets, QtCore

import IceSpringDemoPlugin.demoTranslation as tt
from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.pluginWidgetMixin import PluginWidgetMixin


class DemoBetaWidget(QtWidgets.QWidget, PluginWidgetMixin):
    def __init__(self):
        super().__init__()
        self._app = App.instance()
        self.setLayout(QtWidgets.QGridLayout(self))
        self._label = QtWidgets.QLabel()
        self._label.setAlignment(gg(QtCore.Qt.AlignmentFlag.AlignCenter))
        self.layout().addWidget(self._label)
        self._refreshView()
        self._app.languageChanged.connect(self._refreshView)

    def _refreshView(self):
        self._label.setText(tt.PluginsMenu_ThisIs.format(tt.DemoBetaWidget_Name))
