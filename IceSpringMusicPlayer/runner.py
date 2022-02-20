# Created by BaiJiFeiLong@gmail.com at 2022-01-03 12:55:48

__import__("os").environ.update(dict(
    QT_API="pyside2",
    QT_MULTIMEDIA_PREFERRED_PLUGINS='WindowsMediaFoundation'.lower()
))

import importlib.util
import re
import sys
import types

sys.path.append("pylib")

for moduleName in "pydub.utils", "pydub.audio_segment":
    spec = importlib.util.find_spec(moduleName, None)
    source = spec.loader.get_source(moduleName)
    snippet = "__import__('subprocess').STARTUPINFO(dwFlags=__import__('subprocess').STARTF_USESHOWWINDOW)"
    source = re.sub(r"(Popen)\((.+?)\)", rf"\1(\2, startupinfo=print('worked') or {snippet})", source, flags=re.DOTALL)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, module.__spec__.origin, "exec"), module.__dict__)
    sys.modules[moduleName] = module
module = importlib.reload(sys.modules["pydub"])
for k, v in module.__dict__.items():
    if isinstance(v, types.ModuleType):
        setattr(module, k, importlib.import_module(v.__name__))

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.utils.logUtils import LogUtils


def run() -> None:
    LogUtils.initLogging()
    App().exec_()
