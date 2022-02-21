import importlib.util
import logging
import os
import shutil
import sys
from subprocess import Popen, PIPE

import PyInstaller.__main__
from IceSpringPathLib import Path
from PyInstaller.utils.hooks import collect_submodules

from IceSpringMusicPlayer.utils.logUtils import LogUtils

LogUtils.initLogging()
logging.getLogger().setLevel(logging.INFO)

name = "IceSpringMusicPlayer"
logging.info("Removing application directory if exists...")
Path(f"dist/{name}").rmtree(ignore_errors=True)

logging.info("Checking for backup directory...")
if Path(f"dist/{name}-backup").exists():
    logging.info("Backup directory exists, restoring it...")
    Path(f"dist/{name}-backup").copytree(Path(f"dist/{name}"))
else:
    logging.info("Backup directory not exists, regenerating it...")
    imports = collect_submodules('IceSpringMusicPlayer') + ["statistics", "scipy.signal"]
    hiddenImports = [("--hidden-import", x) for x in imports]
    hiddenImports = [y for x in hiddenImports for y in x]
    PyInstaller.__main__.run(["main.py", "--noconsole", "--noupx", *hiddenImports, "--name", name])
    Path(f"dist/{name}").copytree(Path(f"dist/{name}-backup"))

logging.info("Change directory to application root")
os.chdir(f"dist/{name}")
logging.info("Extract pyinstaller package...")
os.system(f"{sys.executable} ../../resources/pyinstxtractor.py {name}.exe")

logging.info("Copying 3rd libraries to pylib...")
root = Path(f"{name}.exe_extracted/PYZ-00.pyz_extracted")
for path in Path(root).glob("**/*.pyc"):
    if path.relative_to(root).parts[0] == name:
        continue
    module = ".".join(x.split(".pyc")[0] for x in path.relative_to(root).parts if x != "__init__.pyc")
    origin = importlib.util.find_spec(module, None).origin
    if not module == "importlib._bootstrap":
        assert origin is not None
    origin = Path(origin) if origin not in [None, "frozen"] else path
    target = Path("pylib") / path.relative_to(root).with_suffix(origin.suffix)
    logging.debug("Copying %s => %s", origin, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origin, target)

logging.info("Copying application source files...")
for path in Path(f"../../{name}").glob("**/*.py"):
    target = path.relative_to("../..")
    logging.debug("Copying %s => %s", path.absolute(), target.absolute())
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
shutil.copyfile("../../main.py", "main.py")

logging.info("Moving python dynamic libraries to pydll...")
for path in Path().glob("*"):
    if path.name.endswith(".exe_extracted"):
        continue
    if path.name in ("pylib", "pydll", name):
        continue
    if path.is_dir() or path.suffix == ".pyd":
        target = Path("pydll") / path
        logging.debug("Moving %s => %s", path.absolute(), target.absolute())
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.move(str(path), str(target))

logging.info("Merging pydll to pylib...")
for path in Path("pydll").glob("**/*"):
    target = Path("pylib") / path.relative_to("pydll")
    logging.debug("Copying %s => %s", path.absolute(), target.absolute())
    if path.is_file() and not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, target)

logging.info("Copying resources....")
for path in Path("../../resources").glob("**/*"):
    if path.suffix in (".ico", ".png"):
        target = path.relative_to("../..")
        target.parent.mkdir(parents=True, exist_ok=True)
        logging.info("Copying resource %s => %s", path, target)
        shutil.copyfile(path, target)

logging.info("Copying ffmpeg....")
ffmpegPath = Path(r"~\scoop\apps\ffmpeg\current\bin\ffmpeg.exe").expanduser()
shutil.copyfile(ffmpegPath, "ffmpeg.exe")

logging.info("Compiling exe...")
vs = r"C:\Program Files (x86)\Microsoft Visual Studio\2019"
python = Path(r"~\scoop\apps\python37\current").expanduser()
flag = "/SUBSYSTEM:windows /ENTRY:mainCRTStartup"
commands = rf"""
cd ../../resources
"{vs}"\BuildTools\VC\Auxiliary\Build\vcvarsall.bat x86_amd64
rc.exe resources.rc
cl.exe /c main.c -I {python}\include
cl.exe main.obj /link /LIBPATH {python}\libs\python37.lib resources.res {flag}
del main.obj resources.res
""".strip().splitlines()
proc = Popen("cmd", stdin=PIPE, stdout=PIPE, stderr=PIPE)
for command in commands:
    logging.info("Executing command: %s", command)
    proc.stdin.write(f"{command}\n".encode("ansi"))
out, err = proc.communicate()
logging.info("Compiled result: %d", proc.returncode)

logging.info("Moving exe...")
Path(f"{name}.exe").unlink()
shutil.move("../../resources/main.exe", f"{name}.exe")

logging.info("Cleaning...")
excluded_files = "Qt5DataVisualization.dll Qt5Pdf.dll Qt5Quick.dll Qt5VirtualKeyboard.dll d3dcompiler_47.dll " \
                 f"libGLESv2.dll opengl32sw.dll base_library.zip {name}.exe_extracted pydll".split()
for file in Path().glob("*"):
    if file.name in excluded_files:
        if file.is_dir():
            logging.info(f"Removing folder %s...", file.name)
            shutil.rmtree(file)
        else:
            logging.info(f"Removing file %s...", file.name)
            file.unlink()

Path(f"{name}.7z").unlink(missing_ok=True)
os.system(f"cd ../../dist && 7z a -mx=9 ../{name}.7z {name}")
