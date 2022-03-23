from __future__ import unicode_literals
import logging
import os
import glob
import xlrd

logger = logging.getLogger(__name__)


class verifyFileIntegrity:
    def __init__(self, cwd):
        self.cwd = cwd

    def check_files(self):
        directories = next(os.walk('Daily Stock Analysis'))[1]

        for directory in directories:
            for file in glob.glob(fr'{self.cwd}\\Daily Stock Analysis\\{directory}\*.xlsx'):
                file_name = file.split("\\")[-1]

                try:
                    xlrd.open_workbook(file)
                except xlrd.XLRDError as e:
                    logger.debug(f"Error: {e}, file \"{file_name}\" is being removed")
                    os.remove(file)
