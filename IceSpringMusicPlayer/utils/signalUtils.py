# Created by BaiJiFeiLong@gmail.com at 2022/1/20 22:08

import uuid

from PySide2 import QtCore


class SignalUtils(object):
    @classmethod
    def createSignal(cls, *args):
        holder = type("", (QtCore.QObject,), dict(signal=QtCore.Signal(*args)))()
        setattr(cls, str(uuid.uuid4()), holder)
        return holder.signal
