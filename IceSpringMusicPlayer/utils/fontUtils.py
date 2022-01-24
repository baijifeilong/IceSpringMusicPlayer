# Created by BaiJiFeiLong@gmail.com at 2022/1/24 16:35
from PySide2 import QtGui


class FontUtils(object):
    @staticmethod
    def digestFont(font: QtGui.QFont) -> str:
        features = [font.family()]
        font.bold() and features.append("Bold")
        font.italic() and features.append("Italic")
        font.underline() and features.append("Underline")
        font.strikeOut() and features.append("Strike Out")
        len(features) == 1 and features.append("Regular")
        features.append(f"{font.pointSize()} pt")
        return " ".join(features)
