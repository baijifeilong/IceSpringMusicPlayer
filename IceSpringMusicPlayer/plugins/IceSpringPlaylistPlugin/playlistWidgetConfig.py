# Created by BaiJiFeiLong@gmail.com at 2022/2/14 14:52
from __future__ import annotations

import dataclasses

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport


@dataclasses.dataclass
class PlaylistWidgetConfig(JsonSupport):
    rowHeight: int
    horizontalScrollBarPolicy: str
    verticalScrollBarPolicy: str
    showTabBar: bool

    @classmethod
    def getDefaultObject(cls) -> PlaylistWidgetConfig:
        return cls(rowHeight=45, horizontalScrollBarPolicy="AUTO", verticalScrollBarPolicy="AUTO", showTabBar=True)
