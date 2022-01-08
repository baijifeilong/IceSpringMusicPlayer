# Created by BaiJiFeiLong@gmail.com at 2022-01-08 09:05:36

import logging

import colorlog


class LogUtils(object):
    @staticmethod
    def initLogging():
        consoleLogPattern = "%(log_color)s%(asctime)s %(levelname)8s %(name)-16s %(message)s"
        logging.getLogger().handlers = [logging.StreamHandler()]
        logging.getLogger().handlers[0].setFormatter(colorlog.ColoredFormatter(consoleLogPattern))
        logging.getLogger().setLevel(logging.DEBUG)
