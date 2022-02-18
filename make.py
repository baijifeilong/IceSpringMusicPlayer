import os
import pathlib
import shutil

import PyInstaller.__main__
from IceSpringPathLib import Path
from PyInstaller.utils.hooks import collect_submodules

name = "IceSpringMusicPlayer"
ffmpegPath = Path(r"~\scoop\apps\ffmpeg\current\bin\ffmpeg.exe").expanduser()

excluded_files = """
Qt5DataVisualization.dll
Qt5Pdf.dll
Qt5Quick.dll
Qt5VirtualKeyboard.dll
d3dcompiler_47.dll
libGLESv2.dll
opengl32sw.dll
""".strip().splitlines()

imports = collect_submodules('IceSpringMusicPlayer')
imports += ["statistics", "scipy.signal"]
hiddenImports = [("--hidden-import", x) for x in imports]

print("Building...")
if pathlib.Path("dist").exists():
    print("Folder dist exists, removing...")
    shutil.rmtree("dist")

if pathlib.Path(f"{name}.7z").exists():
    print("Target archive exists, removing...")
    pathlib.Path(f"{name}.7z").unlink()

print("Packing...")
PyInstaller.__main__.run([
    "main.py",
    "--noconsole",
    "--noupx",
    *(y for x in hiddenImports for y in x),
    "--name",
    name,
    "--ico",
    "resources/ice.ico",
    "--add-data",
    "resources;resources",
    "--add-data",
    "IceSpringMusicPlayer/plugins;IceSpringMusicPlayer/plugins",
    "--add-data",
    f"{ffmpegPath};.",
])

print("Cleaning...")
for file in pathlib.Path("dist").glob("*/*"):
    if file.name in excluded_files:
        print(f"Removing {file.name}")
        file.unlink()

os.system(f"cd dist && 7z a -mx=9 ../{name}.7z {name}")
