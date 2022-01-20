# Created by BaiJiFeiLong@gmail.com at 2022/1/20 13:41
import dataclasses
import typing

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class DemoMasterConfig(JsonSupport):
    id: str
    prefix: str

    @classmethod
    def pythonToJson(cls, obj: typing.Any) -> typing.Any:
        return super().pythonToJson(obj)

    @classmethod
    def jsonToPython(cls, pairs: typing.List[typing.Tuple[str, typing.Any]]) -> typing.Any:
        jd = dict(pairs)
        if "id" in jd:
            return cls(**jd)
        return jd

    @classmethod
    def getDefaultInstance(cls) -> JsonSupport:
        from IceSpringDemoWidget.demoWidget import DemoWidget
        return DemoMasterConfig(id=".".join((DemoWidget.__module__, DemoWidget.__name__)), prefix="Prefix1")
