# Created by BaiJiFeiLong@gmail.com at 2022/1/22 19:42

from PySide2 import QtWidgets


class HumanLabel(QtWidgets.QLabel):
    def __init__(self, text: str = "", parent: QtWidgets.QWidget = None):
        super().__init__("\u200b".join(text), parent)
        self.setWordWrap(True)

    def setText(self, arg__1: str) -> None:
        super().setText("\u200b".join(arg__1))

    def text(self) -> str:
        return super().text().replace("\u200b", "")
