# Created by BaiJiFeiLong@gmail.com at 2022/2/22 21:11
import importlib.util
import re
import sys
import types


class PydubUtils(object):
    @staticmethod
    def patchPydub():
        for moduleName in "pydub.utils", "pydub.audio_segment":
            spec = importlib.util.find_spec(moduleName, None)
            source = spec.loader.get_source(moduleName)
            info = "__import__('subprocess').STARTUPINFO(dwFlags=__import__('subprocess').STARTF_USESHOWWINDOW)"
            source = re.sub(r"(Popen)\((.+?)\)", rf"\1(\2, startupinfo={info})", source,
                flags=re.DOTALL)
            module = importlib.util.module_from_spec(spec)
            exec(compile(source, module.__spec__.origin, "exec"), module.__dict__)
            sys.modules[moduleName] = module
        module = importlib.reload(sys.modules["pydub"])
        for k, v in module.__dict__.items():
            if isinstance(v, types.ModuleType):
                setattr(module, k, importlib.import_module(v.__name__))
