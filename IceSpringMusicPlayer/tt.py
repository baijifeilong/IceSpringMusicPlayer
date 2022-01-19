# Created by BaiJiFeiLong@gmail.com at 2022/1/19 13:44

class _TT(str):
    en_US: str
    zh_CN: str


Menu_File = _TT()
Menu_File.en_US = "&File"
Menu_File.zh_CN = "文件"
Menu_File_Open = _TT()
Menu_File_Open.en_US = "&Open"
Menu_File_Open.zh_CN = "打开"
Menu_View = _TT()
Menu_View.en_US = "&View"
Menu_View.zh_CN = "视图"
Menu_View_PlaylistManager = _TT()
Menu_View_PlaylistManager.en_US = "&Playlist Manager"
Menu_View_PlaylistManager.zh_CN = "播放列表管理器"
Menu_Layout = _TT()
Menu_Layout.en_US = "&Layout"
Menu_Layout.zh_CN = "布局"
Menu_Layout_ControlsDown = _TT()
Menu_Layout_ControlsDown.en_US = "&Playlist + Lyrics + Controls"
Menu_Layout_ControlsDown.zh_CN = "播放列表 + 歌词 + 控制器"
Menu_Layout_ControlsUp = _TT()
Menu_Layout_ControlsUp.en_US = "&Controls + Playlist + Lyrics"
Menu_Layout_ControlsUp.zh_CN = "控制器 + 播放列表 + 歌词"
Menu_Layout_Default = _TT()
Menu_Layout_Default.en_US = "&Default Layout"
Menu_Layout_Default.zh_CN = "默认布局"
Menu_Layout_Demo = _TT()
Menu_Layout_Demo.en_US = "De&mo Layout"
Menu_Layout_Demo.zh_CN = "演示布局"
Menu_Language = _TT()
Menu_Language.en_US = "Lan&guage"
Menu_Language.zh_CN = "语言"
Menu_Language_English = _TT()
Menu_Language_English.en_US = "&English"
Menu_Language_English.zh_CN = "英文"
Menu_Language_Chinese = _TT()
Menu_Language_Chinese.en_US = "&Chinese (Simplified)"
Menu_Language_Chinese.zh_CN = "简体中文"
Menu_Test = _TT()
Menu_Test.en_US = "Test"
Menu_Test.zh_CN = "测试"
Menu_Test_OneKeyAdd = _TT()
Menu_Test_OneKeyAdd.en_US = "One Key Add Musics"
Menu_Test_OneKeyAdd.zh_CN = "一键添加音乐"
Menu_Test_LoadTestData = _TT()
Menu_Test_LoadTestData.en_US = "Load Test Data"
Menu_Test_LoadTestData.zh_CN = "加载测试数据"
Toolbar_Playlist = _TT()
Toolbar_Playlist.en_US = "Playlist: "
Toolbar_Playlist.zh_CN = "播放列表："
Toolbar_Editing = _TT()
Toolbar_Editing.en_US = "Layout Editing"
Toolbar_Editing.zh_CN = "布局编辑"
Config_ApplicationFont = _TT()
Config_ApplicationFont.en_US = "Application Font"
Config_ApplicationFont.zh_CN = "应用程序字体"
Config_LyricFont = _TT()
Config_LyricFont.en_US = "Lyric Font"
Config_LyricFont.zh_CN = "歌词字体"
Music_Artist = _TT()
Music_Artist.en_US = "Artist"
Music_Artist.zh_CN = "艺术家"
Music_Title = _TT()
Music_Title.en_US = "Title"
Music_Title.zh_CN = "标题"


def setupLanguage(language: str):
    assert language in _TT.__annotations__
    entries = {k: v for k, v in globals().items() if isinstance(v, _TT)}
    for k, v in entries.items():
        tt = _TT(getattr(v, language, getattr(v, "en_US")))
        for lang in _TT.__annotations__:
            if hasattr(v, lang):
                setattr(tt, lang, getattr(v, lang))
        globals()[k] = tt
