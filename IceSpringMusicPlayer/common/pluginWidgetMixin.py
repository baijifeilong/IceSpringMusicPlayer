# Created by BaiJiFeiLong@gmail.com at 2022/1/21 13:41

from __future__ import annotations

import typing

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.common.replacerMixin import ReplacerMixin


class PluginWidgetMixin(ReplacerMixin):
    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[JsonSupport]:
        return JsonSupport

    def getWidgetConfig(self) -> JsonSupport:
        return self.getWidgetConfigClass().getDefaultObject()
