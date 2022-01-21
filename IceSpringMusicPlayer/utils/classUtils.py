# Created by BaiJiFeiLong@gmail.com at 2022/1/21 23:03

class ClassUtils(object):

    @staticmethod
    def fullname(_type: type):
        return ".".join((_type.__module__, _type.__name__))
