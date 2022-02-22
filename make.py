import importlib.util
import logging
import os
import re
import shutil
import sys
from subprocess import Popen, PIPE

import PyInstaller.__main__
from IceSpringPathLib import Path
from PyInstaller.utils.hooks import collect_submodules

from IceSpringMusicPlayer.utils.logUtils import LogUtils

name = "IceSpringMusicPlayer"
vsHome = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2019").absolute()
ffmpegHome = Path("./ffmpeg").absolute()
assert vsHome.exists()
assert ffmpegHome.exists()

LogUtils.initLogging()
logging.getLogger().setLevel(logging.INFO)
logging.info("Removing application directory if exists...")
Path(f"dist/{name}").exists() and Path(f"dist/{name}").rmtree()

logging.info("Checking for backup directory...")
if Path(f"dist/{name}-backup").exists():
    logging.info("Backup directory exists, restoring it...")
    Path(f"dist/{name}-backup").copytree(Path(f"dist/{name}"))
else:
    logging.info("Backup directory not exists, regenerating it...")
    imports = collect_submodules('IceSpringMusicPlayer') + ["statistics", "scipy.signal"]
    hiddenImports = [("--hidden-import", x) for x in imports]
    hiddenImports = [y for x in hiddenImports for y in x]
    PyInstaller.__main__.run(["main.py", "--noupx", "-d", "noarchive", *hiddenImports, "--name", name])
    Path(f"dist/{name}").copytree(Path(f"dist/{name}-backup"))

logging.info("Change directory to application root")
os.chdir(f"dist/{name}")

logging.info("Unzipping base_library.zip...")
shutil.unpack_archive("base_library.zip")

logging.info("Moving python dependencies to Lib...")
for path in Path().glob("*"):
    if path.is_dir() or path.suffix in (".pyc", ".pyd"):
        target = Path("Lib") / path
        logging.debug("Moving %s => %s", path.absolute(), target.absolute())
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.move(str(path), str(target))

logging.info("Adding lost modules...")
for module in ("site", "_sitebuiltins"):
    origin = Path(importlib.util.find_spec(module).origin)
    logging.info("Copying file %s...", origin)
    shutil.copyfile(origin, f"Lib/{origin.name}")

logging.info("Removing application compiled files")
shutil.rmtree(f"Lib/{name}")

removingPyc = True
logging.info("Remove pyc enabled: %s", removingPyc)
if removingPyc:
    logging.info("Changing .pyc/.pyo to .py...")
    count = 0
    for path in Path("Lib").glob("**/*"):
        if path.suffix not in (".pyc", ".pyo"):
            continue
        if "__pycache__" in path.parts:
            continue
        module = ".".join(x for x in path.relative_to("Lib").with_suffix("").parts if x != "__init__")
        origin = importlib.util.find_spec(module).origin
        if origin is not None and Path(origin).exists() and Path(origin).suffix == ".py":
            count += 1
            path.unlink()
            logging.debug("Copying %d %s => %s", count, origin, path.with_suffix(".py"))
            shutil.copyfile(origin, path.with_suffix(".py"))
    logging.info("%d .pyc/.pyo files processed", count)

logging.info("Copying application source files...")
for path in Path(f"../../{name}").glob("**/*.py"):
    target = path.relative_to("../..")
    logging.debug("Copying %s => %s", path.absolute(), target.absolute())
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
shutil.copyfile("../../main.py", "main.py")

logging.info("Copying resources....")
for path in Path("../../resources").glob("**/*"):
    if path.suffix in (".ico", ".png"):
        target = path.relative_to("../..")
        target.parent.mkdir(parents=True, exist_ok=True)
        logging.info("Copying resource %s => %s", path, target)
        shutil.copyfile(path, target)

logging.info("Copying ffmpeg....")
for file in ffmpegHome.glob("*"):
    if re.match(r"^(ffmpeg\.exe|ffprobe\.exe|.+\.dll)$", file.name):
        shutil.copyfile(file, file.name)

logging.info("Compiling exe...")
flag = "/SUBSYSTEM:windows /ENTRY:mainCRTStartup"
commands = rf"""
cd ../../resources
"{vsHome}"\BuildTools\VC\Auxiliary\Build\vcvarsall.bat x86_amd64
rc.exe resources.rc
cl.exe /c main.c -I {sys.base_prefix}\include
cl.exe /Fe{name}.exe main.obj resources.res /link /LIBPATH {sys.base_prefix}\libs\python37.lib {flag}
cl.exe /Fe{name}Debug.exe main.obj resources.res /link /LIBPATH {sys.base_prefix}\libs\python37.lib
del main.obj resources.res
""".strip().splitlines()
proc = Popen("cmd", stdin=PIPE, stdout=PIPE, stderr=PIPE)
for command in commands:
    logging.info("Executing: %s", command)
    proc.stdin.write(f"{command}\n".encode("ansi"))
out, err = proc.communicate()
logging.info("Compiled result: %d", proc.returncode)

logging.info("Moving exe...")
Path(f"{name}.exe").unlink()
shutil.move(f"../../resources/{name}.exe", f"{name}.exe")
shutil.move(f"../../resources/{name}Debug.exe", f"{name}Debug.exe")
shutil.copyfile(f"{sys.base_prefix}/python.exe", "python.exe")

logging.info("Cleaning...")
excluded_files = "Qt5DataVisualization.dll Qt5Pdf.dll Qt5Quick.dll Qt5VirtualKeyboard.dll d3dcompiler_47.dll " \
                 f"libGLESv2.dll opengl32sw.dll base_library.zip {name}.exe_extracted pydll".split()
for filename in excluded_files:
    file = Path(filename)
    if file.exists():
        logging.info(f"Removing %s...", file.name)
        shutil.rmtree(file) if file.is_dir() else file.unlink()

Path(f"../../{name}.7z").unlink(missing_ok=True)
os.system(f"cd ../../dist && 7z a -mx=9 ../{name}.7z {name}")
