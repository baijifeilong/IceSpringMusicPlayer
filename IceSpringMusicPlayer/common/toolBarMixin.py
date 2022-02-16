# Created by BaiJiFeiLong@gmail.com at 2022/2/16 10:29
from IceSpringMusicPlayer.tt import Text


class ToolBarMixin(object):
    @classmethod
    def getToolBarTitle(cls) -> Text:
        raise NotImplementedError
