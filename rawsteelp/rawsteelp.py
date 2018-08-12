#! /usr/bin/env python3

import json
import pathlib
import random
import re
import sys
import taglib
import time
from enum import Enum
from typing import List, Dict, Tuple

import chardet
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *


class Config(object):
    config_path = pathlib.Path('~/.config/rawsteel-music-player').expanduser()
    config_path.parent.mkdir(parents=True) if not config_path.parent.exists() else None

    def __init__(self):
        super().__init__()
        self.playbackMode = MyPlaylist.PlaybackMode.LOOP
        self.playlist: List[MusicEntry] = list()
        self.volume = 50
        self.currentIndex = -1
        self.sortBy = 'ARTIST'
        self.sortOrder = 'ASCENDING'

    @staticmethod
    def load():
        print("Prepare to load config ...")
        config = Config()
        if Config.config_path.exists():
            print("Loading config ...")
            jd = json.loads(Config.config_path.read_text())
            config.playbackMode = MyPlaylist.PlaybackMode(jd['playbackMode'])
            for item in jd['playlist']:
                config.playlist.append(MusicEntry(
                    pathlib.Path(item['path']),
                    item['artist'],
                    item['title'],
                    item['duration']
                ))
            config.volume = jd['volume']
            config.currentIndex = jd['currentIndex']
            config.sortBy = jd['sortBy']
            config.sortOrder = jd['sortOrder']
        else:
            print("Config not exist")
        return config

    def persist(self):
        print("Persisting config ...")
        jd = dict(
            playbackMode=self.playbackMode.value,
            playlist=[dict(path=str(x.path), artist=x.artist, title=x.title, duration=x.duration)
                      for x in self.playlist],
            volume=self.volume,
            currentIndex=self.currentIndex,
            sortBy=self.sortBy,
            sortOrder=self.sortOrder
        )
        jt = json.dumps(jd, indent=4, ensure_ascii=False)
        self.config_path.write_text(jt)


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
        line = re.sub('(\d{2})\d\]', '\\1]', line)
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
    musics_found_signal = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()
        self.music_files: List[pathlib.Path] = list()

    def run(self) -> None:
        print("Loading playlist...")
        count = len(self.music_files)
        musics = list()
        for index, f in enumerate(self.music_files):
            # print("Scanning for {}".format(f))
            artist, title = 'Unknown', 'Unknown'
            if '-' in f.stem: artist, title = f.stem.rsplit('-', maxsplit=1)
            file = taglib.File(str(f))
            artist = file.tags.get('ARTIST', [artist])[0]
            title = file.tags.get('TITLE', [title])[0]
            duration = file.length * 1000
            music_entry = MusicEntry(path=f, artist=artist, title=title, duration=duration)
            # self.music_found_signal.emit((music_entry, count, index + 1))
            time.sleep(0.0001)
            musics.append((music_entry, count, index + 1))
            if len(musics) == 10:
                self.musics_found_signal.emit(musics)
                musics = list()
        if len(musics) > 0:
            self.musics_found_signal.emit(musics)


class MyQSlider(QSlider):

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == Qt.LeftButton:
            self.setValue(self.minimum() + (self.maximum() - self.minimum()) * ev.x() // self.width())
            ev.accept()
        super().mousePressEvent(ev)


class MyQLabel(QLabel):
    clicked = pyqtSignal(QMouseEvent)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.clicked.emit(ev)


class MyAboutDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.resize(400, 300)
        self.setMaximumWidth(30)
        root = QVBoxLayout(self)
        github = 'https://github.com/baijifeilong/rawsteelp'
        pypi = 'https://pypi.org/project/rawsteel-music-player'
        aur = 'https://aur.archlinux.org/packages/rawsteel-music-player'
        label = QLabel('''
        <b>Application</b>: Rawsteel Music Player
        <br>
        <b>Description</b>: A minimal music player with lyric show
        <br>
        <b>Author</b>: BaiJiFeiLong@gmail.com 
        <br>
        <b>Github source</b>: <a href="{0}">{0}</a>
        <br>
        <b>Python PyPI</b>: <a href="{1}">{1}</a>
        <br>
        <b>ArchLinux AUR</b>: <a href="{2}">{2}</a>
        <br>
        <b>License</b>: GPL3
        <br>
        <b>Powered by</b>: <em>Python</em> and <em>Qt</em>
        '''.strip().format(github, pypi, aur), self)
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        label.setOpenExternalLinks(True)
        button = QPushButton('OK', self)
        about_qt = QPushButton("About Qt", self)
        button.clicked.connect(self.close)
        about_qt.clicked.connect(lambda: QMessageBox.aboutQt(self))
        bottom = QHBoxLayout(self)
        bottom.addStretch(1)
        bottom.addWidget(about_qt)
        bottom.addWidget(button)
        root.addWidget(label)
        root.addLayout(bottom)
        self.setWindowTitle("About")
        self.setLayout(root)


class MyPlaylist(QObject):
    current_index_changed = pyqtSignal(int)
    volume_changed = pyqtSignal(int)
    playing_changed = pyqtSignal(bool)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)

    class PlaybackMode(Enum):
        LOOP = 1
        RANDOM = 2

    def __init__(self) -> None:
        super().__init__()
        self._player = QMediaPlayer()
        self._playlist = QMediaPlaylist()
        self._musics: List[MusicEntry] = list()
        self._current_index = -1
        self._playback_mode = MyPlaylist.PlaybackMode.LOOP
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

    def remove_music(self, index):
        del self._musics[index]

    def clear(self):
        self._musics.clear()

    def music(self, index):
        return self._musics[index]

    def musics(self):
        return self._musics

    def play(self):
        if self.music_count() == 0:
            return
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
        if self.music_count() == 0:
            self.set_current_index(-1)
        elif self._playback_mode == self.PlaybackMode.LOOP:
            self.set_current_index(self._current_index - 1 if self._current_index > 0 else self.music_count() - 1)
        else:
            self._history_index -= 1
            if (self._history_index not in self._history) or self._history[self._history_index] >= self.music_count():
                self._history[self._history_index] = self._next_random_index()
            self.set_current_index(self._history[self._history_index])

    def next(self):
        if self.music_count() == 0:
            self.set_current_index(-1)
        elif self._playback_mode == self.PlaybackMode.LOOP:
            self.set_current_index(self._current_index + 1 if self._current_index < self.music_count() - 1 else 0)
        else:
            self._history_index += 1
            if (self._history_index not in self._history) or self._history[self._history_index] >= self.music_count():
                self._history[self._history_index] = self._next_random_index()
            self.set_current_index(self._history[self._history_index])

    def _next_random_index(self):
        current_index = self._current_index
        next_index = random.randint(0, self.music_count() - 1)
        while self.music_count() > 1 and next_index == current_index:
            next_index = random.randint(0, self.music_count() - 1)
        return next_index

    def music_count(self):
        return len(self._musics)

    def set_current_index(self, index):
        self._current_index = index
        if index > -1:
            music = self._musics[index]
            self._player.blockSignals(True)
            self._player.setMedia(QMediaContent(QUrl.fromLocalFile(str(music.path))))
            self._player.blockSignals(False)
            if self._history_index == -1 and len(self._history) == 0:
                self._history[self._history_index] = index
        else:
            self._player.blockSignals(True)
            self._player.stop()
            self._player.blockSignals(False)
        self.current_index_changed.emit(index)

    def current_index(self):
        return self._current_index

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
        self.lyric_label: MyQLabel = None
        self.progress_dialog: QProgressDialog = None
        self.my_playlist: MyPlaylist = MyPlaylist()
        self.load_playlist_task = LoadPlaylistTask()
        self.musics: List[MusicEntry] = list()
        self.lyric: Dict[int, str] = None
        self.prev_lyric_index = -1
        self.config: Config = None
        self.real_row = -1
        self.mime_db = QMimeDatabase()
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
        self.load_playlist_task.music_found_signal.connect(self.add_music)
        self.load_playlist_task.musics_found_signal.connect(self.add_musics)
        self.play_button.clicked.connect(self.toggle_play)
        self.prev_button.clicked.connect(self.on_play_previous)
        self.next_button.clicked.connect(self.on_play_next)
        self.playback_mode_button.clicked.connect(lambda: self.on_playback_mode_button_clicked())
        self.progress_slider.valueChanged.connect(self.on_progress_slider_value_changed)
        self.volume_dial.valueChanged.connect(self.on_volume_dial_value_changed)
        self.my_playlist.playing_changed.connect(self.on_playing_changed)
        self.my_playlist.position_changed.connect(self.on_player_position_changed)
        self.my_playlist.duration_changed.connect(self.on_player_duration_changed)
        self.my_playlist.current_index_changed.connect(self.on_playlist_current_index_changed)
        self.playlist_widget.doubleClicked.connect(self.dbl_clicked)
        self.lyric_label.clicked.connect(self.on_lyric_clicked)

    def on_lyric_clicked(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.lyric is None:
                return
            loc = self.lyric_label.mapFromGlobal(self.lyric_label.cursor().pos())
            line = len(self.lyric) * loc.y() // self.lyric_label.height()
            print("clicked", line)
            time = sorted(self.lyric.items())[line][0]
            self.my_playlist.set_position(time)
        elif event.button() == Qt.RightButton:
            menu = QMenu()
            menu.addAction("About")
            menu.triggered.connect(lambda: MyAboutDialog(self).exec())
            menu.exec(QCursor.pos())
            menu.clear()

    def on_play_next(self):
        self.my_playlist.next()
        self.my_playlist.play()

    def on_play_previous(self):
        self.my_playlist.previous()
        self.my_playlist.play()

    def on_volume_dial_value_changed(self, value):
        self.set_volume(value)
        self.config.volume = value
        self.config.persist()

    def set_volume(self, volume):
        self.volume_dial.blockSignals(True)
        self.my_playlist.set_volume(volume)
        self.volume_dial.setValue(volume)
        self.volume_dial.blockSignals(False)

    def on_playback_mode_button_clicked(self):
        if self.my_playlist.get_playback_mode() == MyPlaylist.PlaybackMode.RANDOM:
            self.set_playback_mode(MyPlaylist.PlaybackMode.LOOP)
        else:
            self.set_playback_mode(MyPlaylist.PlaybackMode.RANDOM)
        self.config.persist()

    def set_playback_mode(self, playback_mode: MyPlaylist.PlaybackMode):
        self.config.playbackMode = playback_mode
        if playback_mode == MyPlaylist.PlaybackMode.LOOP:
            self.my_playlist.set_playback_mode(MyPlaylist.PlaybackMode.LOOP)
            self.playback_mode_button.setIcon(QIcon.fromTheme('media-playlist-repeat'))
        else:
            self.my_playlist.set_playback_mode(MyPlaylist.PlaybackMode.RANDOM)
            self.playback_mode_button.setIcon(QIcon.fromTheme('media-playlist-shuffle'))

    def on_progress_slider_value_changed(self, value):
        self.my_playlist.set_position(value * 1000)

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
        print("Playlist index changed: {}".format(index))
        self.config.currentIndex = index
        self.config.persist()
        if index == -1:
            self.lyric = None
            self.lyric_label.setText("<center><em>No music</em></center>")
            self.setWindowTitle('')
            return
        self.progress_slider.setValue(0)
        self.playlist_widget.selectRow(index)
        self.prev_lyric_index = -1
        music = self.my_playlist.music(index)
        self.setWindowTitle('{} - {}'.format(music.artist, music.title))
        music_file = music.path
        lyric_file: pathlib.PosixPath = music_file.parent / (music_file.stem + '.lrc')
        if lyric_file.exists():
            bys = lyric_file.read_bytes()
            encoding = chardet.detect(bys)['encoding']
            try:
                lyric_text = str(bys, encoding='GB18030')
            except UnicodeDecodeError:
                lyric_text = str(bys, encoding=encoding)
            self.lyric = parse_lyric(lyric_text)
            if len(self.lyric) > 0:
                self.refresh_lyric()
            else:
                self.lyric = None
        else:
            self.lyric = None
            print("Lyric file not found.")

    def refresh_lyric(self):
        hbar = self.lyric_wrapper.horizontalScrollBar()
        hbar.hide()
        self.lyric_wrapper.horizontalScrollBar().setValue((hbar.maximum() + hbar.minimum()) // 2)
        if self.lyric is None:
            self.lyric_label.setText("<center><em>Lyric not found or not supported</em></center>")
            return
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
        self.lyric_wrapper.horizontalScrollBar().setValue((hbar.maximum() + hbar.minimum()) // 2)

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
        self.config = Config.load()
        self.set_playback_mode(self.config.playbackMode)
        self.set_volume(self.config.volume)
        sort_by = dict(ARTIST=0, TITLE=1, DURATION=2)[self.config.sortBy]
        sort_order = Qt.AscendingOrder if self.config.sortOrder == 'ASCENDING' else Qt.DescendingOrder
        self.playlist_widget.horizontalHeader().setSortIndicator(sort_by, sort_order)
        for index, music in enumerate(self.config.playlist):
            self.add_music((music, len(self.config.playlist), index + 1), with_progress=False)
        if len(self.config.playlist) > 0 and self.config.currentIndex >= 0:
            self.my_playlist.set_current_index(self.config.currentIndex)

    def add_musics(self, musics):
        for music in musics:
            self.add_music(music)

    def add_music(self, entry, with_progress=True):
        music: MusicEntry = entry[0]
        total: int = entry[1]
        current: int = entry[2]
        # print("Add : {}".format(music.path))
        self.progress_dialog.show()
        if total < 300 or current % 3 == 0:
            self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(music.path.stem + music.path.suffix)
        # if any([x.path == music.path for x in self.my_playlist.musics()]):
        #     return
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
        if current == total:
            self.progress_dialog.setValue(total)
            self.playlist_widget.scrollToBottom()
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
        self.playlist_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_widget.customContextMenuRequested.connect(self.on_request_context_menu)
        self.lyric_wrapper = QScrollArea(self)
        self.lyric_label = MyQLabel('<center>Hello, World!</center>')
        font = self.lyric_label.font()
        font.setPointSize(14)
        self.lyric_label.setFont(font)
        self.lyric_wrapper.setWidget(self.lyric_label)
        self.lyric_wrapper.setWidgetResizable(True)
        self.lyric_wrapper.verticalScrollBar().hide()
        self.init_progress_dialog()

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
        self.setAcceptDrops(True)

    def on_request_context_menu(self):
        print("Requesting...")
        menu = QMenu()
        menu.addAction("Delete")
        menu.triggered.connect(self.remove_music)
        menu.exec(QCursor.pos())
        menu.clear()

    def remove_music(self):
        current_index = self.my_playlist.current_index()
        playing = self.my_playlist.is_playing()
        indices = sorted(list(set([x.row() for x in self.playlist_widget.selectedIndexes()])), reverse=True)
        for index in indices:
            self.my_playlist.remove_music(index)
            self.playlist_widget.removeRow(index)
            print("Removing index={}, currentIndex={}".format(index, current_index))
        self.config.persist()
        if current_index in indices:
            if self.my_playlist.music_count() > 0:
                self.my_playlist.next()
            else:
                self.my_playlist.set_current_index(-1)
            if playing:
                self.my_playlist.play()

    def init_progress_dialog(self):
        self.progress_dialog = QProgressDialog(self)
        # noinspection PyTypeChecker
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setWindowTitle("Loading music")
        self.progress_dialog.setFixedSize(444, 150)
        self.progress_dialog.setModal(True)
        self.progress_dialog.setValue(100)

    def on_sort_ended(self):
        self.my_playlist.clear()
        for row in range(self.playlist_widget.rowCount()):
            music: MusicEntry = self.playlist_widget.item(row, 0).data(Qt.UserRole)
            self.my_playlist.add_music(music)
        self.config.playlist = self.my_playlist.musics()
        self.config.sortBy = {0: 'ARTIST', 1: 'TITLE', 2: 'DURATION'}[
            self.playlist_widget.horizontalHeader().sortIndicatorSection()]
        self.config.sortOrder = 'ASCENDING' if \
            self.playlist_widget.horizontalHeader().sortIndicatorOrder() == Qt.AscendingOrder else 'DESCENDING'
        self.config.persist()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        if self.lyric:
            self.prev_lyric_index = -1
            self.refresh_lyric()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        urls: List[QUrl] = event.mimeData().urls()
        paths = [pathlib.Path(x.path()) for x in urls if self.mime_db.mimeTypeForUrl(x).name().startswith('audio/')]
        self.load_playlist_task.music_files = paths
        self.load_playlist_task.start()
        self.init_progress_dialog()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Rawsteel Music Player')
    app.setApplicationDisplayName('Rawsteel Music Player')
    app.setWindowIcon(QIcon.fromTheme('audio-headphones'))
    window = PlayerWindow()
    window.show()
    try:
        app.exec()
    except Exception as e:
        print("Exception", e)


if __name__ == '__main__':
    main()
