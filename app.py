#! /usr/bin/env python3

import pathlib
import sys
from typing import List

from PyQt5 import QtGui
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


class MyQSlider(QSlider):

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == Qt.LeftButton:
            self.setValue(self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
            ev.accept()
        super().mousePressEvent(ev)


class PlayerWindow(QWidget):
    play_button: QToolButton
    prev_button: QToolButton
    next_button: QToolButton
    playback_mode_button: QToolButton
    progress_slider: MyQSlider
    progress_label: QLabel
    dial: QDial
    playlist_widget: QTableWidget
    lyric_wrapper: QScrollArea
    load_playlist_task: LoadPlaylistTask
    playlist_files: List[pathlib.PosixPath]
    player: QMediaPlayer
    playlist: QMediaPlaylist
    lyric_label: QLabel

    def __init__(self):
        super().__init__()
        self.setup_layout()
        self.setup_player()
        self.setup_events()
        self.load_playlist_task.start()

    def generate_tool_button(self, icon_name: str) -> QToolButton:
        button = QToolButton(parent=self)
        button.setIcon(QIcon.fromTheme(icon_name))
        button.setIconSize(QSize(50, 50))
        button.setAutoRaise(True)
        return button

    def setup_events(self):
        self.load_playlist_task = LoadPlaylistTask()
        self.load_playlist_task.found_music_signal.connect(lambda x: print('Found', x) or self.add_music(x))
        self.play_button.clicked.connect(lambda: self.toggle_play())
        self.prev_button.clicked.connect(lambda: self.playlist.previous() or self.player.play())
        self.next_button.clicked.connect(lambda: self.playlist.next() or self.player.play())
        self.playback_mode_button.clicked.connect(lambda: self.on_playback_mode_button_clicked())
        self.progress_slider.valueChanged.connect(lambda _: self.on_progress_slider_value_changed(_))
        self.player.stateChanged.connect(lambda _: self.on_player_state_changed(_))
        self.player.positionChanged.connect(lambda _: self.on_player_position_changed(_))
        self.player.durationChanged.connect(lambda _: self.on_player_duration_changed(_))
        self.playlist_widget.doubleClicked.connect(lambda _: self.dbl_clicked(_))
        self.playlist.currentIndexChanged.connect(lambda _: self.on_playlist_current_index_changed(_))

    def on_playback_mode_button_clicked(self):
        if self.playlist.playbackMode() == QMediaPlaylist.Random:
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
            self.playback_mode_button.setIcon(QIcon.fromTheme('media-playlist-repeat'))
        else:
            self.playlist.setPlaybackMode(QMediaPlaylist.Random)
            self.playback_mode_button.setIcon(QIcon.fromTheme('media-playlist-shuffle'))

    def on_progress_slider_value_changed(self, value):
        self.player.blockSignals(True)
        self.player.setPosition(value * 1000)
        self.player.blockSignals(False)

    def on_player_state_changed(self, state: QMediaPlayer.State):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(QIcon.fromTheme('media-playback-pause'))
        else:
            self.play_button.setIcon(QIcon.fromTheme('media-playback-start'))

    def on_player_position_changed(self, position: int):
        current = position // 1000
        total = self.player.duration() // 1000
        self.progress_label.setText(
            '{:02d}:{:02d}/{:02d}:{:02d}'.format(current // 60, current % 60, total // 60, total % 60))
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(current)
        self.progress_slider.blockSignals(False)

    def on_player_duration_changed(self, duration: int):
        total = duration // 1000
        self.progress_slider.setMaximum(total)

    def on_playlist_current_index_changed(self, index):
        self.progress_slider.setValue(0)

    def toggle_play(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def setup_player(self):
        self.playlist_files = list()
        self.playlist = QMediaPlaylist()
        self.playlist.setPlaybackMode(QMediaPlaylist.Random)
        self.player = QMediaPlayer()
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
        self.progress_slider = MyQSlider(Qt.Horizontal, self)
        self.progress_label = QLabel('00:00/00:00', self)
        self.dial = QDial(self)
        self.dial.setFixedSize(50, 50)
        self.playlist_widget = QTableWidget(0, 2, self)
        self.playlist_widget.setHorizontalHeaderLabels(('Artist', 'Song'))
        self.playlist_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.playlist_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lyric_wrapper = QScrollArea(self)
        self.lyric_label = QLabel('<center>Lyrics...</center>')
        font = self.lyric_label.font()
        font.setPointSize(44)
        self.lyric_label.setFont(font)
        self.lyric_wrapper.setWidget(self.lyric_label)
        self.lyric_wrapper.setWidgetResizable(True)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.playlist_widget, 1)
        content_layout.addWidget(self.lyric_wrapper, 1)

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
