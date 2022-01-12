# Created by BaiJiFeiLong@gmail.com at 2022/1/12 11:03

from typing import List, Mapping

from IceSpringRealOptional.generics import T


class ListUtils(object):

    @staticmethod
    def calcIndexMap(oldList: List[T], newList: List[T]) -> Mapping[int, int]:
        oldIndexToItem = {index: item for index, item in enumerate(oldList)}
        itemToNewIndex = {item: index for index, item in enumerate(newList)}
        return {index: itemToNewIndex.get(oldIndexToItem[index], -1) for index in range(len(oldList))}
