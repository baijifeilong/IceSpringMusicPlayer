# Created by BaiJiFeiLong@gmail.com at 2022/1/23 22:00

from __future__ import annotations

import dataclasses

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class ControlsWidgetConfig(JsonSupport):
    iconSize: int

    @classmethod
    def getDefaultObject(cls) -> ControlsWidgetConfig:
        return ControlsWidgetConfig(iconSize=48)
