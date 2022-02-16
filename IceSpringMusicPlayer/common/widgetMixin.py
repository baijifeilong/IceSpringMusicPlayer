# Created by BaiJiFeiLong@gmail.com at 2022/2/16 15:45

from PySide2 import QtCore

from IceSpringMusicPlayer.utils.signalUtils import SignalUtils


class WidgetMixin(object):
    def gcSlot(self: QtCore.QObject, func):
        return SignalUtils.gcSlot(self, func)
