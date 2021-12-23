from clr import AddReference
import logging

logger = logging.getLogger(__name__)


class ExcelFormatting:
    def __init__(self, file_path):
        self.file_name = file_path

    # for some reason this is causing excel files to get corrupted
    def formatting(self):
        return
        #AddReference(r"C:\Users\fabio\source\repos\Excel-Interop\Excel-Interop\bin\Debug\Excel-Interop.dll")
        #import Excel_Interop
        #formatting = Excel_Interop.ExcelFormatting()
        #formatting.Main(self.file_name)
