# Created by BaiJiFeiLong@gmail.com at 2022-01-08 09:06:01

from __future__ import annotations

from typing import *

T = TypeVar("T")


class TypeHintUtils(object):
    @staticmethod
    def gg(x: Any, _type: Type[T]) -> T:
        return x


gg = TypeHintUtils.gg
