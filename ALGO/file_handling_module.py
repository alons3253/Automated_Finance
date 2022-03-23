import datetime
import re
import glob
import os
import psutil
import logging

logger = logging.getLogger(__name__)


class filePruning:
    def __init__(self, cwd):
        self.today = datetime.date.today().strftime("%m-%d-%Y")
        self.cwd = cwd
        self.root_path = fr'{self.cwd}\Daily Stock Analysis'
        self.dir_list = next(os.walk(self.root_path))[1]

    def initialize_directories(self):
        if not os.path.exists(self.root_path):
            os.mkdir(self.root_path)
        for dir in self.dir_list:
            if not os.path.exists(f'{self.root_path}\\{dir}'):
                os.mkdir(f'{self.root_path}\\{dir}')

    def prune_files(self):
        for dir in self.dir_list:
            if dir == 'Stocks':
                continue
            files = glob.glob(fr'{self.root_path}\\{dir}\*')
            if len(files) == 0:
                continue
            for file in files:
                try:
                    re_match = re.search(r'\d{4}-\d{2}-\d{2}', file)
                    date = datetime.datetime.strptime(re_match.group(), '%Y-%m-%d').date()
                    date_cutoff = datetime.date.today() - datetime.timedelta(days=7)
                    if date_cutoff > date:
                        pruned_backup = str(file)
                        os.remove(pruned_backup)
                except AttributeError:
                    continue

    def excel_handler(self):
        for proc in psutil.process_iter():
            if proc.name() == "EXCEL.EXE":
                proc.kill()
