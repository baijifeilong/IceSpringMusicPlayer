# Created by BaiJiFeiLong@gmail.com at 2022/1/19 13:44

import types
import typing


def setupLanguage(language: str, module: typing.Optional[types.ModuleType] = None):
    assert language in Text.__annotations__
    env = globals() if module is None else module.__dict__
    entries = {k: v for k, v in env.items() if isinstance(v, Text)}
    for k, v in entries.items():
        tt = Text(getattr(v, language, getattr(v, "en_US")))
        for lang in Text.__annotations__:
            if hasattr(v, lang):
                setattr(tt, lang, getattr(v, lang))
        env[k] = tt


class Text(str):
    en_US: str
    zh_CN: str

    @classmethod
    def of(cls, en_US, **kwargs):
        text = cls(en_US)
        text.en_US = en_US
        for k, v in kwargs.items():
            setattr(text, k, v)
        return text


Menu_File = Text()
Menu_File.en_US = "&File"
Menu_File.zh_CN = "文件"
Menu_File_Open = Text()
Menu_File_Open.en_US = "&Open"
Menu_File_Open.zh_CN = "打开"
Menu_View = Text()
Menu_View.en_US = "&View"
Menu_View.zh_CN = "视图"
Menu_View_PlaylistManager = Text()
Menu_View_PlaylistManager.en_US = "&Playlist Manager"
Menu_View_PlaylistManager.zh_CN = "播放列表管理器"
Menu_Layout = Text()
Menu_Layout.en_US = "&Layout"
Menu_Layout.zh_CN = "布局"
Menu_Layout_ControlsDown = Text()
Menu_Layout_ControlsDown.en_US = "&Playlist + Lyrics + Controls"
Menu_Layout_ControlsDown.zh_CN = "播放列表 + 歌词 + 控制器"
Menu_Layout_ControlsUp = Text()
Menu_Layout_ControlsUp.en_US = "&Controls + Playlist + Lyrics"
Menu_Layout_ControlsUp.zh_CN = "控制器 + 播放列表 + 歌词"
Menu_Layout_Default = Text()
Menu_Layout_Default.en_US = "&Default Layout"
Menu_Layout_Default.zh_CN = "默认布局"
Menu_Layout_Demo = Text()
Menu_Layout_Demo.en_US = "De&mo Layout"
Menu_Layout_Demo.zh_CN = "演示布局"
Menu_Language = Text()
Menu_Language.en_US = "Lan&guage"
Menu_Language.zh_CN = "语言"
Menu_Language_English = Text()
Menu_Language_English.en_US = "&English"
Menu_Language_English.zh_CN = "英文"
Menu_Language_Chinese = Text()
Menu_Language_Chinese.en_US = "&Chinese (Simplified)"
Menu_Language_Chinese.zh_CN = "简体中文"
Menu_Plugins = Text()
Menu_Plugins.en_US = "Plugins"
Menu_Plugins.zh_CN = "插件"
Menu_Plugins_AboutPlugin = Text()
Menu_Plugins_AboutPlugin.en_US = "About Plugin"
Menu_Plugins_AboutPlugin.zh_CN = "关于插件"
Menu_Test = Text()
Menu_Test.en_US = "Test"
Menu_Test.zh_CN = "测试"
Menu_Test_OneKeyAdd = Text()
Menu_Test_OneKeyAdd.en_US = "One Key Add Musics"
Menu_Test_OneKeyAdd.zh_CN = "一键添加音乐"
Menu_Test_LoadTestData = Text()
Menu_Test_LoadTestData.en_US = "Load Test Data"
Menu_Test_LoadTestData.zh_CN = "加载测试数据"
Toolbar_Playlist = Text()
Toolbar_Playlist.en_US = "Playlist: "
Toolbar_Playlist.zh_CN = "播放列表："
Toolbar_Editing = Text()
Toolbar_Editing.en_US = "Layout Editing"
Toolbar_Editing.zh_CN = "布局编辑"
Toolbar_ToggleLanguage = Text()
Toolbar_ToggleLanguage.en_US = "Toggle Language"
Toolbar_ToggleLanguage.zh_CN = "切换语言"
Config_ApplicationFont = Text()
Config_ApplicationFont.en_US = "Application Font"
Config_ApplicationFont.zh_CN = "应用程序字体"
Config_LyricFont = Text()
Config_LyricFont.en_US = "Lyric Font"
Config_LyricFont.zh_CN = "歌词字体"
Config_Apply = Text()
Config_Apply.en_US = "Apply"
Config_Apply.zh_CN = "应用"
Music_Artist = Text()
Music_Artist.en_US = "Artist"
Music_Artist.zh_CN = "艺术家"
Music_Title = Text()
Music_Title.en_US = "Title"
Music_Title.zh_CN = "标题"
