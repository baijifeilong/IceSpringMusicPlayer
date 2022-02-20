import importlib.util
import logging
import os
import pathlib
import shutil
import sys
from subprocess import Popen, PIPE

import PyInstaller.__main__
from IceSpringPathLib import Path
from PyInstaller.utils.hooks import collect_submodules

from IceSpringMusicPlayer.utils.logUtils import LogUtils

name = "IceSpringMusicPlayer"
projectRoot = Path().absolute()
ffmpegPath = Path(r"~\scoop\apps\ffmpeg\current\bin\ffmpeg.exe").expanduser()
decompiler = Path("resources/pyinstxtractor.py").absolute()
excluded_files = """
Qt5DataVisualization.dll
Qt5Pdf.dll
Qt5Quick.dll
Qt5VirtualKeyboard.dll
d3dcompiler_47.dll
libGLESv2.dll
opengl32sw.dll
base_library.zip
""".strip().splitlines()

LogUtils.initLogging()

logging.info("Building...")
logging.info("Checking for dist directory...")
if pathlib.Path(f"dist/{name}").exists():
    logging.info(f"Folder dist/{name} exists, removing...")
    shutil.rmtree(f"dist/{name}")

logging.info(f"Checking for {name}.7z")
if pathlib.Path(f"{name}.7z").exists():
    logging.info("Target archive exists, removing...")
    pathlib.Path(f"{name}.7z").unlink()

logging.info("Packing...")
imports = collect_submodules('IceSpringMusicPlayer')
imports += ["statistics", "scipy.signal"]
hiddenImports = [("--hidden-import", x) for x in imports]
hiddenImports = [y for x in hiddenImports for y in x]
PyInstaller.__main__.run(["main.py", "--noconsole", "--noupx", *hiddenImports, "--name", name])

logging.info("Change directory to application root")
os.chdir(projectRoot / "dist" / name)

logging.info("Extract pyinstaller package...")
os.system(f"{sys.executable} {decompiler} {name}.exe")

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
for path in (projectRoot / name).glob("**/*.py"):
    target = Path() / path.relative_to(projectRoot)
    logging.debug("Copying %s => %s", path.absolute(), target.absolute())
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
shutil.copyfile(projectRoot / "main.py", "main.py")

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
    target = Path("pylib") / path.relative_to(Path("pydll"))
    logging.debug("Copying %s => %s", path.absolute(), target.absolute())
    if path.is_file() and not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, target)
    else:
        logging.warning("Skipped")

logging.info("Copying resources....")
for path in (projectRoot / "resources").glob("**/*"):
    if path.suffix in (".ico", ".png"):
        target = path.relative_to(projectRoot)
        target.parent.mkdir(parents=True, exist_ok=True)
        logging.info("Copying resource %s => %s", path, target)
        shutil.copyfile(path, target)

logging.info("Copying ffmpeg....")
shutil.copyfile(ffmpegPath, "ffmpeg.exe")

logging.info("Compiling exe...")
logging.info("Changing to resources directory...")
os.chdir(projectRoot / "resources")
vs = r"C:\Program Files (x86)\Microsoft Visual Studio\2019"
python = Path(r"~\scoop\apps\python37\current").expanduser()
flag = "/SUBSYSTEM:windows /ENTRY:mainCRTStartup"
commands = rf"""
"{vs}"\BuildTools\VC\Auxiliary\Build\vcvarsall.bat x86_amd64
rc.exe resources.rc
cl.exe /c main.c -I {python}\include
cl.exe main.obj /link /LIBPATH {python}\libs\python37.lib resources.res {flag}
""".strip().splitlines()
proc = Popen("cmd", stdin=PIPE, stdout=PIPE, stderr=PIPE)
for command in commands:
    print("Executing command", command)
    proc.stdin.write(f"{command}\n".encode("ansi"))
out, err = proc.communicate()
logging.info("STDOUT: %s", out.decode("ansi"))
logging.warning("STDERR: %s", err.decode("ansi"))

os.chdir(projectRoot / "dist" / name)
logging.info("Copying exe...")
shutil.copyfile(projectRoot / "resources" / "main.exe", f"{name}.exe")

logging.info("Removing unused folders")
for folder in (f"{name}.exe_extracted", "pydll"):
    logging.debug(f"Remove folder {folder}")
    shutil.rmtree(folder)

logging.info("Cleaning...")
os.chdir(projectRoot / "dist" / name)
for file in Path().glob("**/*"):
    print(file)
    if file.name in excluded_files:
        logging.info(f"Removing {file.name}")
        file.unlink()

os.chdir(projectRoot)
# os.system(f"cd dist && 7z a -mx=9 ../{name}.7z {name}")
