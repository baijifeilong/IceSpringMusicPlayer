#! /usr/bin/env python3

import pathlib
import re
import sys
from typing import List, Dict, Tuple

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *


def parse_lyric(text: str):
    regex = re.compile('((\[\d{2}:\d{2}.\d{2}\])+)(.+)')
    lyric: Dict[int, str] = dict()
    for line in text.splitlines():
        line = line.strip()
        if line:
            match = regex.match(line)
            if match:
                time_part = match.groups()[0]
                lyric_part = match.groups()[2].strip()
                for i in range(0, len(time_part), 10):
                    this_time = time_part[i:i + 10]
                    minutes, seconds = this_time[1:-1].split(':')
                    milliseconds = int((int(minutes) * 60 + float(seconds)) * 1000)
                    lyric[milliseconds] = lyric_part
    return lyric


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
    volume_dial: QDial
    playlist_widget: QTableWidget
    lyric_wrapper: QScrollArea
    player: QMediaPlayer
    playlist: QMediaPlaylist
    lyric_label: QLabel
    load_playlist_task: LoadPlaylistTask
    playlist_files: List[pathlib.PosixPath]
    lyric: Dict[int, str]
    prev_lyric_index = -1

    def __init__(self):
        super().__init__()
        self.setup_layout()
        self.setup_player()
        self.setup_events()
        self.load_playlist_task.start()
        self.volume_dial.setValue(50)
        self.lyric = None

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
        self.volume_dial.valueChanged.connect(self.player.setVolume)
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
        self.refresh_lyric()

    def on_player_duration_changed(self, duration: int):
        total = duration // 1000
        self.progress_slider.setMaximum(total)

    def on_playlist_current_index_changed(self, index):
        self.progress_slider.setValue(0)
        self.playlist_widget.selectRow(index)
        self.prev_lyric_index = -1
        music_file = self.playlist_files[index]
        lyric_file: pathlib.PosixPath = music_file.parent / (music_file.stem + '.lrc')
        if lyric_file.exists():
            lyric_text = lyric_file.read_text(encoding='gbk')
            print(lyric_text)
            self.lyric = parse_lyric(lyric_text)
            self.refresh_lyric()
        else:
            print("Lyric file not found.")

    def refresh_lyric(self):
        if self.lyric is None: return
        current_lyric_index = self.calc_current_lyric_index()
        if current_lyric_index == self.prev_lyric_index:
            return
        self.prev_lyric_index = current_lyric_index
        print("current index", current_lyric_index)
        text = ''
        for i, (k, v) in enumerate(sorted(self.lyric.items())):
            if i == current_lyric_index:
                text += '<center><b>{}</b></center>'.format(v)
            else:
                text += '<center>{}</center>'.format(v)
        self.lyric_label.setText(text)
        self.lyric_wrapper.verticalScrollBar().setValue(
            self.lyric_label.height() * current_lyric_index // len(self.lyric)
            - self.lyric_wrapper.height() // 2
        )

    def calc_current_lyric_index(self):
        entries: List[Tuple[int, str]] = sorted(self.lyric.items())
        current_position = self.player.position()
        if current_position < entries[0][0]:
            return 0
        for i in range(len(self.lyric) - 1):
            entry = entries[i]
            next_entry = entries[i + 1]
            if entry[0] <= current_position < next_entry[0]:
                return i
        return len(self.lyric) - 1

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
        self.volume_dial = QDial(self)
        self.volume_dial.setFixedSize(50, 50)
        self.playlist_widget = QTableWidget(0, 2, self)
        self.playlist_widget.setHorizontalHeaderLabels(('Artist', 'Song'))
        self.playlist_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.playlist_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.playlist_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.playlist_widget.horizontalHeader().hide()
        self.lyric_wrapper = QScrollArea(self)
        self.lyric_label = QLabel('<center>Hello, World!</center>')
        font = self.lyric_label.font()
        font.setPointSize(14)
        self.lyric_label.setFont(font)
        self.lyric_wrapper.setWidget(self.lyric_label)
        self.lyric_wrapper.setWidgetResizable(True)
        self.lyric_wrapper.verticalScrollBar().hide()

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
        controller_layout.addWidget(self.volume_dial)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(content_layout)
        root_layout.addLayout(controller_layout)

        self.setLayout(root_layout)
        self.resize(888, 666)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        if self.lyric:
            self.prev_lyric_index = -1
            self.refresh_lyric()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Rawsteel Music Player')
    app.setWindowIcon(QIcon.fromTheme('audio-headphones'))
    window = PlayerWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
