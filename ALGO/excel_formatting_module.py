from clr import AddReference


class ExcelFormatting:
    def __init__(self, file_path):
        self.file_name = file_path

    def formatting(self):
        AddReference(r"C:\Users\fabio\source\repos\Excel-Interop\Excel-Interop\bin\Debug\Excel-Interop.dll")
        import Excel_Interop
        formatting = Excel_Interop.ExcelFormatting()
        formatting.Main(self.file_name)
