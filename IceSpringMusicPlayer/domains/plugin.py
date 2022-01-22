# Created by BaiJiFeiLong@gmail.com at 2022/1/22 20:11

from __future__ import annotations

import dataclasses
import typing

from IceSpringMusicPlayer.common.jsonSupport import JsonSupport

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.common.pluginMixin import PluginMixin


@dataclasses.dataclass
class Plugin(object):
    clazz: typing.Type[PluginMixin]
    disabled: bool
    config: JsonSupport
