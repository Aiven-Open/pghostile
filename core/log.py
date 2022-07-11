# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

import logging

__all__ = ["logger"]

def __new_logger(name):
    logger = logging.getLogger(name)
    fileh = logging.FileHandler("%s.log" % name)
    fileh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(fileh)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    return logger


logger = __new_logger("pghostile")