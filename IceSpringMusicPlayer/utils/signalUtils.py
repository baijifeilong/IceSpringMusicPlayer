# Created by BaiJiFeiLong@gmail.com at 2022/1/20 22:08

import uuid

from IceSpringRealOptional.just import Just
from PySide2 import QtCore


class SignalUtils(object):
    @classmethod
    def createSignal(cls, *args):
        return Just.of(type("", (QtCore.QObject,), dict(signal=QtCore.Signal(*args)))()) \
            .apply(lambda x: setattr(cls, str(uuid.uuid4()), x)).value().signal
