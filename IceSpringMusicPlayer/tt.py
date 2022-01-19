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


def setupLanguage(language: str):
    assert language in _TT.__annotations__
    entries = {k: v for k, v in globals().items() if isinstance(v, _TT)}
    for k, v in entries.items():
        tt = _TT(getattr(v, language, getattr(v, "en_US")))
        for lang in _TT.__annotations__:
            if hasattr(v, lang):
                setattr(tt, lang, getattr(v, lang))
        globals()[k] = tt
