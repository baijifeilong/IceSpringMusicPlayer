# Created by BaiJiFeiLong@gmail.com at 2022/1/20 22:23

import typing

from IceSpringMusicPlayer import tt
from IceSpringMusicPlayer.tt import Text

if typing.TYPE_CHECKING:
    from IceSpringMusicPlayer.tt import *


def __getattr__(name):
    return globals().get(name, getattr(tt, name))


Demo_Name = Text()
Demo_Name.en_US = "Demo Plugin"
Demo_Name.zh_CN = "演示插件"
Demo_AboutMe = Text()
Demo_AboutMe.en_US = "About Demo Widget"
Demo_AboutMe.zh_CN = "关于演示插件"
Demo_Description = Text()
Demo_Description.en_US = "This is demo widget"
Demo_Description.zh_CN = "这是演示插件"
DemoWidget_Name = Text()
DemoWidget_Name.en_US = "Demo Widget"
DemoWidget_Name.zh_CN = "演示组件"
Demo_PluginCounter = Text()
Demo_PluginCounter.en_US = "Plugin Counter: "
Demo_PluginCounter.zh_CN = "插件计数器："
Demo_WidgetCounter = Text()
Demo_WidgetCounter.en_US = "Widget Counter: "
Demo_WidgetCounter.zh_CN = "组件计数器："
DemoBetaWidget_Name = Text()
DemoBetaWidget_Name.en_US = "Beta Widget"
DemoBetaWidget_Name.zh_CN = "演示贝塔组件"
