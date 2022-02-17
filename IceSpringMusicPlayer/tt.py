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


FileMenu = Text()
FileMenu.en_US = "&File"
FileMenu.zh_CN = "文件"
FileMenu_AddFiles = Text()
FileMenu_AddFiles.en_US = "Add F&iles"
FileMenu_AddFiles.zh_CN = "添加文件"
FileMenu_AddFolder = Text()
FileMenu_AddFolder.en_US = "Add F&older"
FileMenu_AddFolder.zh_CN = "添加文件夹"
FileMenu_Config = Text()
FileMenu_Config.en_US = "Preferences"
FileMenu_Config.zh_CN = "设置"
EditMenu = Text()
EditMenu.en_US = "&Edit"
EditMenu.zh_CN = "编辑"
EditMenu_SelectAll = Text()
EditMenu_SelectAll.en_US = "Select All"
EditMenu_SelectAll.zh_CN = "选择全部"
EditMenu_RemoveSelection = Text()
EditMenu_RemoveSelection.en_US = "Remove Selection"
EditMenu_RemoveSelection.zh_CN = "移除选择"
ViewMenu = Text()
ViewMenu.en_US = "&View"
ViewMenu.zh_CN = "视图"
ViewMenu_PlaylistManager = Text()
ViewMenu_PlaylistManager.en_US = "&Playlist Manager"
ViewMenu_PlaylistManager.zh_CN = "播放列表管理器"
LayoutMenu = Text()
LayoutMenu.en_US = "&Layout"
LayoutMenu.zh_CN = "布局"
LayoutMenu_Default = Text()
LayoutMenu_Default.en_US = "&Default Layout"
LayoutMenu_Default.zh_CN = "默认布局"
LayoutMenu_Demo = Text()
LayoutMenu_Demo.en_US = "De&mo Layout"
LayoutMenu_Demo.zh_CN = "演示布局"
PlaybackMenu = Text()
PlaybackMenu.en_US = "Playback"
PlaybackMenu.zh_CN = "回放"
PlaybackMenu_Play = Text()
PlaybackMenu_Play.en_US = "Play"
PlaybackMenu_Play.zh_CN = "播放"
PlaybackMenu_Pause = Text()
PlaybackMenu_Pause.en_US = "Pause"
PlaybackMenu_Pause.zh_CN = "暂停"
PlaybackMenu_Stop = Text()
PlaybackMenu_Stop.en_US = "Stop"
PlaybackMenu_Stop.zh_CN = "停止"
PlaybackMenu_Previous = Text()
PlaybackMenu_Previous.en_US = "Previous"
PlaybackMenu_Previous.zh_CN = "上一首"
PlaybackMenu_Next = Text()
PlaybackMenu_Next.en_US = "Next"
PlaybackMenu_Next.zh_CN = "下一首"
PlaybackModeMenu = Text()
PlaybackModeMenu.en_US = "Playback Mode"
PlaybackModeMenu.zh_CN = "回放模式"
PlaybackModeMenu_Loop = Text()
PlaybackModeMenu_Loop.en_US = "Playlist Loop"
PlaybackModeMenu_Loop.zh_CN = "播放列表循环"
PlaybackModeMenu_Random = Text()
PlaybackModeMenu_Random.en_US = "Playlist Random"
PlaybackModeMenu_Random.zh_CN = "播放列表随机"
PlaybackModeMenu_Repeat = Text()
PlaybackModeMenu_Repeat.en_US = "Track Loop"
PlaybackModeMenu_Repeat.zh_CN = "单曲循环"
LanguageMenu = Text()
LanguageMenu.en_US = "Lan&guage"
LanguageMenu.zh_CN = "语言"
LanguageMenu_English = Text()
LanguageMenu_English.en_US = "&English"
LanguageMenu_English.zh_CN = "英文"
LanguageMenu_Chinese = Text()
LanguageMenu_Chinese.en_US = "&Chinese (Simplified)"
LanguageMenu_Chinese.zh_CN = "简体中文"
PluginsMenu = Text()
PluginsMenu.en_US = "Plugins"
PluginsMenu.zh_CN = "插件"
PluginsMenu_AboutPlugin = Text()
PluginsMenu_AboutPlugin.en_US = "About Plugin"
PluginsMenu_AboutPlugin.zh_CN = "关于插件"
PluginsMenu_ConfigPlugin = Text()
PluginsMenu_ConfigPlugin.en_US = "Config Plugin"
PluginsMenu_ConfigPlugin.zh_CN = "配置插件"
PluginsMenu_ThisIs = Text()
PluginsMenu_ThisIs.en_US = "This is {}"
PluginsMenu_ThisIs.zh_CN = "这是 {}"
TestMenu = Text()
TestMenu.en_US = "Test"
TestMenu.zh_CN = "测试"
TestMenu_OneKeyAdd = Text()
TestMenu_OneKeyAdd.en_US = "One Key Add Musics"
TestMenu_OneKeyAdd.zh_CN = "一键添加音乐"
TestMenu_LoadTestData = Text()
TestMenu_LoadTestData.en_US = "Load Test Data"
TestMenu_LoadTestData.zh_CN = "加载测试数据"
TestMenu_ToggleLanguage = Text()
TestMenu_ToggleLanguage.en_US = "Toggle Language"
TestMenu_ToggleLanguage.zh_CN = "切换语言"
HelpMenu = Text()
HelpMenu.en_US = "&Help"
HelpMenu.zh_CN = "帮助"
HelpMenu_About = Text()
HelpMenu_About.en_US = "About"
HelpMenu_About.zh_CN = "关于"
HelpMenu_AboutTitle = Text()
HelpMenu_AboutTitle.en_US = "About IceSpringMusicPlayer"
HelpMenu_AboutTitle.zh_CN = "关于冰泉音乐播放器"
HelpMenu_AboutText = Text()
HelpMenu_AboutText.en_US = "IceSpringMusicPlayer v1.0.0\nBaiJiFeiLong@gmail.com"
HelpMenu_AboutText.zh_CN = "冰泉音乐播放器 v1.0.0\nBaiJiFeiLong@gmail.com"
Toolbar_Menu = Text()
Toolbar_Menu.en_US = "Menu"
Toolbar_Menu.zh_CN = "菜单"
Toolbar_Controller = Text()
Toolbar_Controller.en_US = "Controller"
Toolbar_Controller.zh_CN = "控制器"
Toolbar_Volume = Text()
Toolbar_Volume.en_US = "Volume"
Toolbar_Volume.zh_CN = "音量"
Toolbar_Playlist = Text()
Toolbar_Playlist.en_US = "Playlist"
Toolbar_Playlist.zh_CN = "播放列表"
Toolbar_Progress = Text()
Toolbar_Progress.en_US = "Progress"
Toolbar_Progress.zh_CN = "进度条"
Toolbar_PlaylistLabel = Text()
Toolbar_PlaylistLabel.en_US = "Playlist: "
Toolbar_PlaylistLabel.zh_CN = "播放列表："
Toolbar_Editing = Text()
Toolbar_Editing.en_US = "Layout Editing"
Toolbar_Editing.zh_CN = "布局编辑"
Toolbar_Lock = Text()
Toolbar_Lock.en_US = "Lock %s"
Toolbar_Lock.zh_CN = "锁定%s"
Toolbar_LockAll = Text()
Toolbar_LockAll.en_US = "Lock All"
Toolbar_LockAll.en_US = "锁定全部"
Toolbar_UnlockAll = Text()
Toolbar_UnlockAll.en_US = "Unlock All"
Toolbar_UnlockAll.zh_CN = "解锁全部"
Config_ApplicationFont = Text()
Config_ApplicationFont.en_US = "Application Font"
Config_ApplicationFont.zh_CN = "应用程序字体"
Config_LyricFont = Text()
Config_LyricFont.en_US = "Lyric Font"
Config_LyricFont.zh_CN = "歌词字体"
Config_Apply = Text()
Config_Apply.en_US = "Apply"
Config_Apply.zh_CN = "应用"
Config_QuickBrownFox = Text()
Config_QuickBrownFox.en_US = "The quick brown fox jumps over the lazy dog."
Config_QuickBrownFox.zh_CN = "天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。"
Music_Artist = Text()
Music_Artist.en_US = "Artist"
Music_Artist.zh_CN = "艺术家"
Music_Title = Text()
Music_Title.en_US = "Title"
Music_Title.zh_CN = "标题"
HelloWorldPlugin_Name = Text()
HelloWorldPlugin_Name.en_US = "Hello World Plugin"
HelloWorldPlugin_Name.zh_CN = "你好世界插件"
HelloWorldWidget_Name = Text()
HelloWorldWidget_Name.en_US = "Hello World Widget"
HelloWorldWidget_Name.zh_CN = "你好世界组件"
Plugins_ConfigWidget = Text()
Plugins_ConfigWidget.en_US = "Config Widget"
Plugins_ConfigWidget.zh_CN = "组件配置"
Plugins_ToggleFullscreen = Text()
Plugins_ToggleFullscreen.en_US = "Toggle Fullscreen"
Plugins_ToggleFullscreen.zh_CN = "切换全屏"
MaskWidget_ReplaceWithBlankWidget = Text()
MaskWidget_ReplaceWithBlankWidget.en_US = "Replace With Blank Widget"
MaskWidget_ReplaceWithBlankWidget.zh_CN = "替换为空白组件"
MaskWidget_HorizontallySplitTo = Text()
MaskWidget_HorizontallySplitTo.en_US = "Horizontally Split To"
MaskWidget_HorizontallySplitTo.zh_CN = "水平分割为"
MaskWidget_VerticallySplitTo = Text()
MaskWidget_VerticallySplitTo.en_US = "Vertically Split To"
MaskWidget_VerticallySplitTo.zh_CN = "垂直分割为"
MaskWidget_QuitEditingMode = Text()
MaskWidget_QuitEditingMode.en_US = "Quit Editing Mode"
MaskWidget_QuitEditingMode.zh_CN = "退出编辑模式"
MaskWidget_NColumns = Text()
MaskWidget_NColumns.en_US = "{} Columns"
MaskWidget_NColumns.zh_CN = "{} 列"
MaskWidget_NRows = Text()
MaskWidget_NRows.en_US = "{} Rows"
MaskWidget_NRows.zh_CN = "{} 行"
