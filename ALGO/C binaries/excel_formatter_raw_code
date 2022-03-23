using System;
using Excel = Microsoft.Office.Interop.Excel;


namespace Excel_Interop
{
    public class ExcelFormatting
    {
        public static void ExcelRun(String filename)
        {
            Excel.Application excelApp = new Excel.Application
            {
                Visible = false,
                DisplayAlerts = true
            };

            Excel.Workbooks xlWorkbooks = excelApp.Workbooks;
            Excel.Workbook xlWorkbook = xlWorkbooks.Open(filename, 0, false, 1, "", "", true, Excel.XlPlatform.xlWindows, "\t", false, false, 0, true, 1, 0);

            try
            {
                foreach (Excel.Worksheet worksheet in xlWorkbook.Worksheets)
                {
                    worksheet.Columns.AutoFit();
                    worksheet.Rows.AutoFit();
                }
            }
            catch (Exception Ex)
            {
                Console.Write("Exception caught: {0}", Ex);
            }
            finally
            {
                GC.Collect();
                GC.WaitForPendingFinalizers();

                System.Runtime.InteropServices.Marshal.FinalReleaseComObject(xlWorkbooks);

                xlWorkbook.Close(true, Type.Missing, Type.Missing);
                //xlWorkbook.Close(SaveChanges: true, Filename: filename);
                System.Runtime.InteropServices.Marshal.FinalReleaseComObject(xlWorkbook);

                excelApp.Quit();
                System.Runtime.InteropServices.Marshal.FinalReleaseComObject(excelApp);
            }
        }

        public static void Main(String args)
        {
            String filename = args;
            ExcelRun(filename);
        }
    }
}
