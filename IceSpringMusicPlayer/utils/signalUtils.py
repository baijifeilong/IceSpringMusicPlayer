# Created by BaiJiFeiLong@gmail.com at 2022/1/20 22:08
import inspect
import uuid

from IceSpringRealOptional.just import Just
from PySide2 import QtCore
from assertpy import assert_that


class SignalUtils(object):
    @classmethod
    def createSignal(cls, *args):
        return Just.of(type("", (QtCore.QObject,), dict(signal=QtCore.Signal(*args)))()) \
            .apply(lambda x: setattr(cls, str(uuid.uuid4()), x)).value().signal

    @staticmethod
    def gcSlot(instance: QtCore.QObject, func):
        assert_that(len(inspect.getfullargspec(func).args)).is_greater_than_or_equal_to(1)
        assert_that(inspect.getfullargspec(func).args[0]).is_equal_to("self")
        _type = type(instance)
        _name = f"__slot_{id(func)}"
        instance.destroyed.connect(lambda: setattr(_type, _name, None))
        setattr(_type, _name, func)
        return getattr(instance, _name)
