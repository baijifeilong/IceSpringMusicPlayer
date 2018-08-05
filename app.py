#! /usr/bin/env python3
import pathlib
import sys
from typing import List

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *


class LoadPlaylistTask(QThread):
    found_music_signal = pyqtSignal(pathlib.PosixPath)

    def run(self) -> None:
        print("Loading playlist...")
        for f in pathlib.Path('/mnt/d/music/test').iterdir():
            if f.suffix != '.lrc':
                self.found_music_signal.emit(f)


class PlayerWindow(QWidget):
    play_button: QToolButton
    prev_button: QToolButton
    next_button: QToolButton
    playback_mode_button: QToolButton
    progress_slider: QSlider
    progress_label: QLabel
    dial: QDial
    playlist_widget: QTableWidget
    lyric_wrapper: QScrollArea
    load_playlist_task: LoadPlaylistTask
    playlist_files: List[pathlib.PosixPath]
    player: QMediaPlayer
    playlist: QMediaPlaylist

    def __init__(self):
        super().__init__()
        self.setup_layout()
        self.setup_events()
        self.setup_player()

    def generate_tool_button(self, icon_name: str) -> QToolButton:
        button = QToolButton(parent=self)
        button.setIcon(QIcon.fromTheme(icon_name))
        button.setIconSize(QSize(50, 50))
        button.setAutoRaise(True)
        return button

    def setup_events(self):
        self.load_playlist_task = LoadPlaylistTask()
        self.load_playlist_task.found_music_signal.connect(lambda x: print('Found', x) or self.add_music(x))
        self.play_button.clicked.connect(lambda: self.load_playlist_task.start())
        self.playlist_widget.doubleClicked.connect(lambda _: self.dbl_clicked(_))

    def setup_player(self):
        self.playlist_files = list()
        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)

    def add_music(self, music_file: pathlib.PosixPath):
        row = self.playlist_widget.rowCount()
        stem = music_file.stem
        artist, song = stem.split('-')
        self.playlist_widget.insertRow(row)
        self.playlist_widget.setItem(row, 0, QTableWidgetItem(artist))
        self.playlist_widget.setItem(row, 1, QTableWidgetItem(song))
        self.playlist_files.append(music_file)
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(music_file))))

    def dbl_clicked(self, item: QModelIndex):
        self.playlist.setCurrentIndex(item.row())
        self.player.play()
        pass

    def setup_layout(self):
        self.play_button = self.generate_tool_button('media-playback-start')
        self.prev_button = self.generate_tool_button('media-skip-backward')
        self.next_button = self.generate_tool_button('media-skip-forward')
        self.playback_mode_button = self.generate_tool_button('media-playlist-shuffle')
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_label = QLabel('00:00/00:00', self)
        self.dial = QDial(self)
        self.dial.setFixedSize(50, 50)
        self.playlist_widget = QTableWidget(0, 2, self)
        self.playlist_widget.setHorizontalHeaderLabels(('Artist', 'Song'))
        self.playlist_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.playlist_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lyric_wrapper = QScrollArea(self)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.playlist_widget)
        content_layout.addWidget(self.lyric_wrapper)

        controller_layout = QHBoxLayout()
        controller_layout.addWidget(self.play_button)
        controller_layout.addWidget(self.prev_button)
        controller_layout.addWidget(self.next_button)
        controller_layout.addWidget(self.progress_slider)
        controller_layout.addWidget(self.progress_label)
        controller_layout.addWidget(self.playback_mode_button)
        controller_layout.addWidget(self.dial)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(content_layout)
        root_layout.addLayout(controller_layout)

        self.setLayout(root_layout)
        self.resize(888, 666)


def main():
    app = QApplication(sys.argv)
    window = PlayerWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
