# Created by BaiJiFeiLong@gmail.com at 2022/1/20 16:00

from __future__ import annotations

import abc
import typing


class JsonSupport(object, metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def pythonToJson(cls, obj: typing.Any) -> typing.Any:
        return obj.__dict__

    @classmethod
    @abc.abstractmethod
    def jsonToPython(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]) -> typing.Any:
        return dict(pairs)

    @classmethod
    @abc.abstractmethod
    def getDefaultInstance(cls) -> JsonSupport:
        return cls()
