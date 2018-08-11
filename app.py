#! /usr/bin/env python3

import pathlib
import random
import re
import sys
import taglib
import time
from typing import List, Dict, Tuple

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *


class MusicEntry(object):

    def __init__(self, path, artist, title, duration) -> None:
        super().__init__()
        self.path: pathlib.PosixPath = path
        self.artist: str = artist
        self.title: str = title
        self.duration: int = duration


def parse_lyric(text: str):
    regex = re.compile('((\[\d{2}:\d{2}.\d{2}\])+)(.+)')
    lyric: Dict[int, str] = dict()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = regex.match(line)
        if not match: continue
        time_part = match.groups()[0]
        lyric_part = match.groups()[2].strip()
        for i in range(0, len(time_part), 10):
            this_time = time_part[i:i + 10]
            minutes, seconds = this_time[1:-1].split(':')
            milliseconds = int((int(minutes) * 60 + float(seconds)) * 1000)
            lyric[milliseconds] = lyric_part
    return lyric


class LoadPlaylistTask(QThread):
    music_found_signal = pyqtSignal(tuple)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        print("Loading playlist...")
        files = [f for f in pathlib.Path('/mnt/d/music/test').iterdir() if f.suffix != '.lrc']
        count = len(files)
        for index, f in enumerate(files):
            if f.suffix != '.lrc':
                # print("Scanning for {}".format(f))
                artist, title = 'Unknown', 'Unknown'
                if '-' in f.stem: artist, title = f.stem.split('-')
                file = taglib.File(str(f))
                artist = file.tags.get('ARTIST', [artist])[0]
                title = file.tags.get('TITLE', [title])[0]
                duration = file.length * 1000
                music_entry = MusicEntry(path=f, artist=artist, title=title, duration=duration)
                self.music_found_signal.emit((music_entry, count, index + 1))
                time.sleep(0.01)


class MyQSlider(QSlider):

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == Qt.LeftButton:
            self.setValue(self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
            ev.accept()
        super().mousePressEvent(ev)


class MyPlaylist(QObject):
    current_index_changed = pyqtSignal(int)
    volume_changed = pyqtSignal(int)
    playing_changed = pyqtSignal(bool)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)

    LOOP = 1
    RANDOM = 2

    def __init__(self) -> None:
        super().__init__()
        self._player = QMediaPlayer()
        self._playlist = QMediaPlaylist()
        self._musics: List[MusicEntry] = list()
        self._current_index = -1
        self._playback_mode = MyPlaylist.LOOP
        self._playing = False
        self._player.positionChanged.connect(self.position_changed.emit)
        self._player.durationChanged.connect(self.duration_changed.emit)
        self._player.stateChanged.connect(self._on_player_state_changed)
        self._history: Dict[int, int] = dict()
        self._history_index = -1

    def _on_player_state_changed(self, state):
        print("STATE CHANGED")
        if state == QMediaPlayer.StoppedState:
            print("STOPPED")
            self.next()
            self.play()

    def add_music(self, music: MusicEntry):
        self._musics.append(music)

    def clear(self):
        self._musics.clear()

    def music(self, index):
        return self._musics[index]

    def play(self):
        if self._current_index == -1:
            self.set_current_index(0)
        self._player.play()
        self._playing = True
        self.playing_changed.emit(self._playing)

    def pause(self):
        self._player.pause()
        self._playing = False
        self.playing_changed.emit(self._playing)

    def previous(self):
        if self._playback_mode == self.LOOP:
            self.set_current_index(self._current_index - 1 if self._current_index > 0 else self.music_count() - 1)
        else:
            self._history_index -= 1
            if self._history_index not in self._history:
                self._history[self._history_index] = self._next_random_index()
            self.set_current_index(self._history[self._history_index])

    def next(self):
        if self._playback_mode == self.LOOP:
            self.set_current_index(self._current_index + 1 if self._current_index < self.music_count() - 1 else 0)
        else:
            self._history_index += 1
            if self._history_index not in self._history:
                self._history[self._history_index] = self._next_random_index()
            self.set_current_index(self._history[self._history_index])

    def _next_random_index(self):
        current_index = self._current_index
        next_index = random.randint(0, self.music_count())
        while self.music_count() > 1 and next_index == current_index:
            next_index = random.randint(0, self.music_count())
        return next_index

    def music_count(self):
        return len(self._musics)

    def set_current_index(self, index):
        self._current_index = index
        music = self._musics[index]
        self._player.blockSignals(True)
        self._player.setMedia(QMediaContent(QUrl.fromLocalFile(str(music.path))))
        self._player.blockSignals(False)
        self.current_index_changed.emit(index)

    def get_playback_mode(self):
        return self._playback_mode

    def set_playback_mode(self, mode):
        self._playback_mode = mode

    def get_volume(self):
        return self._player.volume()

    def set_volume(self, volume):
        self._player.setVolume(volume)
        self.volume_changed.emit(volume)

    def get_position(self):
        return self._player.position()

    def set_position(self, position):
        self._player.setPosition(position)

    def get_duration(self):
        return self._player.duration()

    def is_playing(self):
        return self._playing

    def index_of(self, music: MusicEntry):
        return self._musics.index(music)


class PlayerWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.play_button: QToolButton = None
        self.prev_button: QToolButton = None
        self.next_button: QToolButton = None
        self.playback_mode_button: QToolButton = None
        self.progress_slider: MyQSlider = None
        self.progress_label: QLabel = None
        self.volume_dial: QDial = None
        self.playlist_widget: QTableWidget = None
        self.lyric_wrapper: QScrollArea = None
        self.lyric_label: QLabel = None
        self.progress_dialog: QProgressDialog = None
        self.my_playlist: MyPlaylist = MyPlaylist()
        self.load_playlist_task = LoadPlaylistTask()
        self.musics: List[MusicEntry] = list()
        self.lyric: Dict[int, str] = None
        self.prev_lyric_index = -1
        self.setup_layout()
        self.setup_player()
        self.setup_events()
        self.volume_dial.setValue(50)
        self.load_playlist_task.start()
        self.progress_dialog.show()

    def generate_tool_button(self, icon_name: str) -> QToolButton:
        button = QToolButton(parent=self)
        button.setIcon(QIcon.fromTheme(icon_name))
        button.setIconSize(QSize(50, 50))
        button.setAutoRaise(True)
        return button

    def setup_events(self):
        self.load_playlist_task.music_found_signal.connect(self.add_music)
        self.play_button.clicked.connect(lambda: self.toggle_play())
        self.prev_button.clicked.connect(lambda: self.my_playlist.previous() or self.my_playlist.play())
        self.next_button.clicked.connect(lambda: self.my_playlist.next() or self.my_playlist.play())
        self.playback_mode_button.clicked.connect(lambda: self.on_playback_mode_button_clicked())
        self.progress_slider.valueChanged.connect(self.on_progress_slider_value_changed)
        self.volume_dial.valueChanged.connect(self.my_playlist.set_volume)
        self.my_playlist.playing_changed.connect(self.on_playing_changed)
        self.my_playlist.position_changed.connect(self.on_player_position_changed)
        self.my_playlist.duration_changed.connect(self.on_player_duration_changed)
        self.playlist_widget.doubleClicked.connect(self.dbl_clicked)
        self.my_playlist.current_index_changed.connect(self.on_playlist_current_index_changed)

    def on_playback_mode_button_clicked(self):
        if self.my_playlist.get_playback_mode() == MyPlaylist.RANDOM:
            self.my_playlist.set_playback_mode(MyPlaylist.LOOP)
            self.playback_mode_button.setIcon(QIcon.fromTheme('media-playlist-repeat'))
        else:
            self.my_playlist.set_playback_mode(MyPlaylist.RANDOM)
            self.playback_mode_button.setIcon(QIcon.fromTheme('media-playlist-shuffle'))

    def on_progress_slider_value_changed(self, value):
        self.my_playlist.blockSignals(True)
        self.my_playlist.set_position(value * 1000)
        self.my_playlist.blockSignals(False)

    def on_playing_changed(self, playing: bool):
        if playing:
            self.play_button.setIcon(QIcon.fromTheme('media-playback-pause'))
        else:
            self.play_button.setIcon(QIcon.fromTheme('media-playback-start'))

    def on_player_position_changed(self, position: int):
        current = position // 1000
        total = self.my_playlist.get_duration() // 1000
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
        music_file = self.my_playlist.music(index).path
        lyric_file: pathlib.PosixPath = music_file.parent / (music_file.stem + '.lrc')
        if lyric_file.exists():
            lyric_text = lyric_file.read_text(encoding='gbk')
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
        current_position = self.my_playlist.get_position()
        if current_position < entries[0][0]:
            return 0
        for i in range(len(self.lyric) - 1):
            entry = entries[i]
            next_entry = entries[i + 1]
            if entry[0] <= current_position < next_entry[0]:
                return i
        return len(self.lyric) - 1

    def toggle_play(self):
        if self.my_playlist.is_playing():
            self.my_playlist.pause()
        else:
            self.my_playlist.play()

    def setup_player(self):
        self.my_playlist.set_playback_mode(MyPlaylist.RANDOM)

    def add_music(self, entry):
        music: MusicEntry = entry[0]
        total: int = entry[1]
        current: int = entry[2]
        row = self.playlist_widget.rowCount()
        self.playlist_widget.setSortingEnabled(False)
        self.playlist_widget.insertRow(row)
        self.playlist_widget.setItem(row, 0, QTableWidgetItem(music.artist))
        self.playlist_widget.setItem(row, 1, QTableWidgetItem(music.title))
        self.playlist_widget.setItem(row, 2, QTableWidgetItem(
            '{:02d}:{:02d}'.format(music.duration // 60000, music.duration // 1000 % 60)))
        self.playlist_widget.item(row, 0).setData(Qt.UserRole, music)
        # print("current: {}, last: {}".format(music.title, last_music.title))
        self.my_playlist.add_music(music)
        self.progress_dialog.setMaximum(total)
        self.progress_dialog.setValue(current)
        # noinspection PyTypeChecker
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setLabelText(music.path.stem + music.path.suffix)
        self.playlist_widget.scrollToBottom()
        if current == total:
            self.playlist_widget.setSortingEnabled(True)
            last_music: MusicEntry = self.playlist_widget.item(current - 1, 0).data(Qt.UserRole)
            print("current: {}, last: {}".format(music.title, last_music.title))
            self.on_sort_ended()

    def dbl_clicked(self, item: QModelIndex):
        self.my_playlist.set_current_index(item.row())
        self.my_playlist.play()

    def setup_layout(self):
        self.play_button = self.generate_tool_button('media-playback-start')
        self.prev_button = self.generate_tool_button('media-skip-backward')
        self.next_button = self.generate_tool_button('media-skip-forward')
        self.playback_mode_button = self.generate_tool_button('media-playlist-shuffle')
        self.progress_slider = MyQSlider(Qt.Horizontal, self)
        self.progress_label = QLabel('00:00/00:00', self)
        self.volume_dial = QDial(self)
        self.volume_dial.setFixedSize(50, 50)
        self.playlist_widget = QTableWidget(0, 3, self)
        self.playlist_widget.setHorizontalHeaderLabels(('Artist', 'Title', 'Duration'))
        self.playlist_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.playlist_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.playlist_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.playlist_widget.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.playlist_widget.horizontalHeader().sectionClicked.connect(self.on_sort_ended)
        self.lyric_wrapper = QScrollArea(self)
        self.lyric_label = QLabel('<center>Hello, World!</center>')
        font = self.lyric_label.font()
        font.setPointSize(14)
        self.lyric_label.setFont(font)
        self.lyric_wrapper.setWidget(self.lyric_label)
        self.lyric_wrapper.setWidgetResizable(True)
        self.lyric_wrapper.verticalScrollBar().hide()
        self.progress_dialog = QProgressDialog()
        self.progress_dialog.setModal(True)
        self.progress_dialog.setWindowTitle("Loading music")
        self.progress_dialog.setFixedSize(444, 150)

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

    def on_sort_ended(self):
        self.my_playlist.clear()
        for row in range(self.playlist_widget.rowCount()):
            music: MusicEntry = self.playlist_widget.item(row, 0).data(Qt.UserRole)
            self.my_playlist.add_music(music)

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
