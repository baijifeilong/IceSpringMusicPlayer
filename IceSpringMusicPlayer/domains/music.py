# Created by BaiJiFeiLong@gmail.com at 2022-01-03 13:16:51
import dataclasses


@dataclasses.dataclass(unsafe_hash=True)
class Music(object):
    filename: str
    filesize: int
    album: str
    artist: str
    title: str
    duration: int
    bitrate: int
    sampleRate: int
    channels: int
    format: str
