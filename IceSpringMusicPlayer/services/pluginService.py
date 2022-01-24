# Created by BaiJiFeiLong@gmail.com at 2022/1/23 18:31

import importlib
import logging
import typing
from datetime import datetime

from IceSpringPathLib import Path
from PySide2 import QtCore

from IceSpringMusicPlayer.app import App
from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
from IceSpringMusicPlayer.domains.config import Element
from IceSpringMusicPlayer.domains.plugin import Plugin


class PluginService(QtCore.QObject):
    pluginEnabled: QtCore.SignalInstance = QtCore.Signal(Plugin)
    pluginDisabled: QtCore.SignalInstance = QtCore.Signal(Plugin)
    pluginsInserted: QtCore.SignalInstance = QtCore.Signal(list)
    pluginsRemoved: QtCore.SignalInstance = QtCore.Signal(list)

    def __init__(self, parent: QtCore.QObject = None):
        super().__init__(parent)
        self._logger = logging.getLogger("pluginService")
        self._app = App.instance()

    def getPluginClasses(self) -> typing.List[typing.Type[PluginMixin]]:
        return self.findPluginClassesInFolder("IceSpringMusicPlayer/plugins")

    def findPluginClassesInFolder(self, folder):
        self._logger.info("Find plugin classes in folder: %s", folder)
        from IceSpringMusicPlayer.common.pluginMixin import PluginMixin
        classes = set()
        pluginRoot = Path("IceSpringMusicPlayer/plugins")
        for path in Path(folder).glob("**/*.py"):
            package = ".".join([x for x in path.relative_to(pluginRoot).parts if x != "__init__.py"]).rstrip(".py")
            for x in importlib.import_module(package).__dict__.values():
                if isinstance(x, type) and issubclass(x, PluginMixin) and x != PluginMixin:
                    classes.add(x)
        return sorted(classes, key=lambda x: x.__module__ + "." + x.__name__)

    def _verifyPluginFolder(self, folder: str) -> typing.List[typing.Type[PluginMixin]]:
        self._logger.info("Verify plugin in folder: %s", folder)
        oldClasses = [x.clazz for x in self._app.getConfig().plugins]
        root = Path(folder)
        if not (root / "__init__.py").exists():
            raise RuntimeError("Plugin folder must contains __init__.py")
        targetPath = Path(f"IceSpringMusicPlayer/plugins/{root.name}")
        if targetPath.exists():
            self._logger.info("Plugin already exists.")
            raise RuntimeError("Plugin Already Exists")
        self._logger.info("Copy plugin folder to plugins dir %s", targetPath)
        root.copytree(targetPath)
        try:
            classes = self.findPluginClassesInFolder(str(targetPath))
            classes = [x for x in classes if x not in oldClasses]
        except Exception as e:
            self._logger.info("Exception occurred: %s", e, e)
            self._logger.info("Remove folder: %s", targetPath)
            targetPath.rmtree()
            raise e
        if len(classes) == 0:
            self._logger.info("No plugin found in folder, remove folder")
            targetPath.rmtree()
            raise RuntimeError("No plugin found")
        return classes

    def addPlugin(self, folder):
        self._logger.info("On add plugin")
        classes = self._verifyPluginFolder(folder)
        assert len(classes) > 0
        if any([x.isSystemPlugin() for x in classes]):
            self._logger.info("System plugins are not allowed to be added")
            raise RuntimeError("System plugins are not allowed to be added")
        self._logger.info("Found %d plugins: %s", len(classes), classes)
        self.registerNewPlugins(classes)

    def registerNewPlugins(self, classes: typing.List[typing.Type[PluginMixin]]) -> None:
        self._logger.info("Register new %d plugins", len(classes))
        oldClasses = [x.clazz for x in self._app.getConfig().plugins]
        for clazz in classes:
            assert clazz not in oldClasses
            self._logger.info("Register plugin %s", clazz)
            self._app.getConfig().plugins.append(Plugin(
                clazz=clazz,
                disabled=False,
                config=clazz.getPluginConfigClass().getDefaultObject()
            ))
        self._logger.info("> Signal pluginInserted emitting...")
        self.pluginsInserted.emit([x for x in self._app.getConfig().plugins if x.clazz in classes])
        self._logger.info("< Signal pluginInserted emitted.")

    def enablePlugin(self, plugin: Plugin):
        self._logger.info("Enable plugin: %s", plugin.clazz)
        assert plugin.disabled
        plugin.disabled = False
        self._logger.info("> Signal pluginEnabled emitting...")
        self.pluginEnabled.emit(plugin)
        self._logger.info("> Signal pluginEnabled emitted.")

    def disablePlugin(self, plugin: Plugin):
        self._logger.info("Disable plugin: %s", plugin.clazz)
        assert not plugin.clazz.isSystemPlugin()
        assert not plugin.disabled
        assert not self.isPluginUsedInMainWindow(plugin), "Plugin used in main window"
        plugin.disabled = True
        self._logger.info("> Signal pluginDisabled emitting...")
        self.pluginDisabled.emit(plugin)
        self._logger.info("> Signal pluginDisabled emitted.")

    def removePlugin(self, plugin: Plugin) -> None:
        self._logger.info("Remove plugin: %s", plugin.clazz)
        assert not plugin.clazz.isSystemPlugin()
        assert not self.isPluginUsedInMainWindow(plugin), "Plugin used in main window"
        stem = plugin.clazz.__module__.split(".")[0]
        path = Path(f"IceSpringMusicPlayer/plugins/{stem}")
        self._logger.info("Remove plugin folder: %s", path)
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        targetPath = Path(f"IceSpringMusicPlayer/recycles/{now}/{stem}")
        self._logger.info("Plugin is backup to %s", targetPath)
        path.copytree(targetPath)
        path.rmtree()
        self._logger.info("Remove plugin from registry")
        self._app.getConfig().plugins.remove(plugin)
        self._logger.info("> Signal pluginRemoved emitting...")
        self.pluginsRemoved.emit([plugin])
        self._logger.info("< Signal pluginRemoved emitted.")

    def isPluginUsedInMainWindow(self, plugin: Plugin):
        layout = self._app.getMainWindow().calcLayout()
        return self._isPluginUsedInElement(plugin, layout)

    def _isPluginUsedInElement(self, plugin: Plugin, element: Element):
        usedInSelf = element.clazz.__module__.startswith(plugin.clazz.__module__)
        usedInChildren = any(self._isPluginUsedInElement(plugin, x) for x in element.children)
        return usedInSelf or usedInChildren
