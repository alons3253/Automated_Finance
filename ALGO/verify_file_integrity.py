from __future__ import unicode_literals
import io
import logging
import os
import glob
import openpyxl
from xlwt import Workbook
import pandas as pd

logger = logging.getLogger(__name__)


class verifyFileIntegrity:
    def __init__(self):
        self.cwd = os.getcwd()
        self.directories = [r'\Bonds', r'\Options', r'\Trades']

    def check_files(self):
        for directory in self.directories:
            for file in glob.glob(self.cwd + r'\Daily Stock Analysis' + directory + r'\*.xlsx'):
                try:
                    openpyxl.load_workbook(file)
                except Exception as e:
                    logger.debug(file)
                    logger.debug(str(e) + " file is being removed")
                    os.remove(file)
