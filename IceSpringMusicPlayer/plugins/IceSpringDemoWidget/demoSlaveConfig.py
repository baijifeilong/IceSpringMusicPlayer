# Created by BaiJiFeiLong@gmail.com at 2022/1/20 15:31
import dataclasses
import typing

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class DemoSlaveConfig(JsonSupport):
    id: str
    suffix: str

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
        clazz = DemoWidget
        return DemoSlaveConfig(id=".".join((clazz.__module__, clazz.__name__)), suffix="Suffix1")
