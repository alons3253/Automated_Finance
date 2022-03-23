from clr import AddReference
import logging

logger = logging.getLogger(__name__)


class ExcelFormatting:
    def __init__(self, file_path):
        self.file_name = file_path

    # for some reason this was causing excel files to be corrupted, should be fixed though
    def formatting(self):
        logging.debug(f"{self.file_name} is being formatted")
        AddReference(r"C:\Users\fabio\source\repos\Excel-Interop\Excel-Interop\bin\Debug\Excel-Interop.dll")
        import Excel_Interop
        formatting = Excel_Interop.ExcelFormatting()
        formatting.Main(self.file_name)
        logging.debug(f"formatting for {self.file_name} is finished")
