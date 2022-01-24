# Created by BaiJiFeiLong@gmail.com at 2022/1/20 22:23

import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


DemoPlugin_Name = Text()
DemoPlugin_Name.en_US = "Demo Plugin"
DemoPlugin_Name.zh_CN = "演示插件"
DemoPlugin_Description = Text()
DemoPlugin_Description.en_US = "This is demo widget"
DemoPlugin_Description.zh_CN = "这是演示插件"
DemoPluginMenu_Config = Text()
DemoPluginMenu_Config.en_US = "Demo Plugin Config"
DemoPluginMenu_Config.zh_CN = "演示插件配置"
DemoWidget_Name = Text()
DemoWidget_Name.en_US = "Demo Widget"
DemoWidget_Name.zh_CN = "演示组件"
DemoWidget_PluginCounter = Text()
DemoWidget_PluginCounter.en_US = "Plugin Counter: "
DemoWidget_PluginCounter.zh_CN = "插件计数器："
DemoWidget_WidgetCounter = Text()
DemoWidget_WidgetCounter.en_US = "Widget Counter: "
DemoWidget_WidgetCounter.zh_CN = "组件计数器："
DemoBetaWidget_Name = Text()
DemoBetaWidget_Name.en_US = "Beta Widget"
DemoBetaWidget_Name.zh_CN = "演示贝塔组件"
