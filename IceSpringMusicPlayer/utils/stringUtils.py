# Created by BaiJiFeiLong@gmail.com at 2022/1/22 9:08
import re


class StringUtils(object):
    @staticmethod
    def camelToTitle(text: str):
        text = re.sub(r"(?<=^)([a-z])", lambda x: x.group(1).upper(), text)
        text = re.sub(r"([A-Z]+)", r" \1", text)
        return text.strip()
