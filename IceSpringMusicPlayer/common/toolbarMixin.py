# Created by BaiJiFeiLong@gmail.com at 2022/2/16 10:29
from IceSpringMusicPlayer.tt import Text


class ToolbarMixin(object):
    @classmethod
    def getToolbarTitle(cls) -> Text:
        raise NotImplementedError
