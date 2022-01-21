# Created by BaiJiFeiLong@gmail.com at 2022/1/20 16:00

from __future__ import annotations

import typing


class JsonSupport(object):
    @classmethod
    def pythonToJson(cls, obj: typing.Any) -> typing.Any:
        return obj.__dict__

    @classmethod
    def jsonToPython(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]) -> typing.Any:
        return dict(pairs)

    @classmethod
    def getDefaultObject(cls) -> JsonSupport:
        return cls()
