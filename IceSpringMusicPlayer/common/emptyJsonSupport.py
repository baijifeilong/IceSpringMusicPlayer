# Created by BaiJiFeiLong@gmail.com at 2022/1/21 13:46
import typing

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


class EmptyJsonSupport(JsonSupport):
    @classmethod
    def pythonToJson(cls, obj: typing.Any) -> typing.Any:
        return super().pythonToJson(obj)

    @classmethod
    def jsonToPython(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]) -> typing.Any:
        return super().jsonToPython(pairs)

    @classmethod
    def getDefaultInstance(cls) -> JsonSupport:
        return super().getDefaultInstance()
