# Created by BaiJiFeiLong@gmail.com at 2022/1/9 11:47

class TimedeltaUtils(object):
    @staticmethod
    def formatDelta(milliseconds) -> str:
        seconds = int(milliseconds) // 1000
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
