# Created by BaiJiFeiLong@gmail.com at 2022/1/21 13:41

from __future__ import annotations

import typing

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport
from IceSpringMusicPlayer.tt import Text
from IceSpringMusicPlayer.widgets.replaceableMixin import ReplaceableMixin


class PluginWidgetMixin(ReplaceableMixin):
    @classmethod
    def getWidgetName(cls) -> Text:
        return Text.of(cls.__name__)

    @classmethod
    def getWidgetConfigClass(cls) -> typing.Type[JsonSupport]:
        return JsonSupport

    def getWidgetConfig(self) -> JsonSupport:
        return self.getWidgetConfigClass().getDefaultObject()
