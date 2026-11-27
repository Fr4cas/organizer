
from pathlib import Path

import pandas as pd

from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableColumn, TableStyleInfo

from scripts.filename_parser import FILENAME_ANOMALY_COLUMNS, MISSING_ID_ANOMALY, FORMAT_ANOMALY
from scripts.comparator import (
    FILE_ANOMALY_COLUMNS,
    SUBJECT_CANDIDATE,
    MULTIPLE_SUBJECT,
    NO_EXCEL_RECORD,
    NO_MATCH,
    DUPLICATE_FILE
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# Single Excel listing reasons offered in the 異常原因 dropdown
REASON_CHOICES = ["單號缺漏", "格式錯誤", "單號重複", "找不到對應檔案"]

# Single anomaly types offered in the 異常類型 dropdowns
FILENAME_TYPE_CHOICES = [MISSING_ID_ANOMALY, FORMAT_ANOMALY]

FILE_TYPE_CHOICES = [
    SUBJECT_CANDIDATE,
    MULTIPLE_SUBJECT,
    NO_EXCEL_RECORD,
    NO_MATCH,
    DUPLICATE_FILE
]


# --------------------------------------------------
# Shared styling
# --------------------------------------------------

def style_header_row(ws):

    header_fill = PatternFill(
        "solid",
        fgColor="4472C4"
    )

    for cell in ws[1]:

        cell.font = Font(
            name="Microsoft JhengHei",
            bold=True,
            color="FFFFFF",
            size=11
        )

        cell.fill = header_fill

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    ws.row_dimensions[1].height = 30


# --------------------------------------------------
# File inventory
# --------------------------------------------------

INVENTORY_COLUMNS = [
    "檔名",
    "擷取單號",
    "擷取主旨",
    "路徑"
]


def build_inventory(parse_results):

    return pd.DataFrame(
        [
            {
                "檔名": file["filename"],
                "擷取單號": file["document_number"],
                "擷取主旨": file["subject"],
                "路徑": str(file["full_path"])
            }
            for file in parse_results["files"]
        ],
        columns=INVENTORY_COLUMNS
    )


# --------------------------------------------------
# 1. Plain table worksheet (File Inventory, Filename Anomalies, File Anomalies)
# --------------------------------------------------

def add_choice_dropdown(ws, column, choices):

    # Single choices plus any combined values present in the sheet
    choices = list(dict.fromkeys(choices))

    formula = '"' + ",".join(choices) + '"'

    # Excel limits a list validation to 255 characters
    if len(formula) > 255:
        print(f"Dropdown skipped for {ws.title} column {column}: too many choices")
        return

    dropdown = DataValidation(
        type="list",
        formula1=formula,
        allow_blank=True,
        showErrorMessage=True,
        errorStyle="warning"
    )

    ws.add_data_validation(dropdown)

    dropdown.add(f"{column}2:{column}{max(ws.max_row, 2)}")


def write_table_sheet(writer, data, sheet_name, widths, filter_column=None):

    data.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False
    )

    ws = writer.sheets[sheet_name]

    style_header_row(ws)

    # Keep text as text (e.g. "=..." must not become a formula)
    for row in ws.iter_rows(min_row=2):

        for cell in row:

            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.data_type = "s"

    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width

    ws.freeze_panes = "A2"
    # Header filter: all columns by default, or only the given column
    if filter_column:
        ws.auto_filter.ref = f"{filter_column}1:{filter_column}{max(ws.max_row, 1)}"
    else:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(data.columns))}{ws.max_row}"


# --------------------------------------------------
# 2. Organized-style worksheet (shared by Organized, 公司收文, 工地收文)
# --------------------------------------------------

def write_organized_sheet(writer, data, sheet_name, table_name):

    data.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False
    )

    ws = writer.sheets[sheet_name]

    # ----------------------------------
    # Column headers
    # ----------------------------------

    style_header_row(ws)

    # ----------------------------------
    # Excel table
    # ----------------------------------

    last_row = ws.max_row

    table = Table(
        displayName=table_name,
        ref=f"A1:E{last_row}"
    )

    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False
    )

    # Set columns ourselves so openpyxl doesn't add an AutoFilter (row 1 dropdowns)
    table.tableColumns = [
        TableColumn(id=index, name=str(cell.value))
        for index, cell in enumerate(ws[1], start=1)
    ]

    ws.add_table(table)

    # ----------------------------------
    # Column widths
    # ----------------------------------

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 65
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 14

    # ----------------------------------
    # Data formatting
    # ----------------------------------

    thin_grey = Side(
        style="hair",
        color="D9E2F3"
    )

    for row in ws.iter_rows(
        min_row=2,
        max_row=last_row
    ):

        for cell in row:

            cell.font = Font(
                name="Microsoft JhengHei",
                size=10,
                color="333333"
            )

            cell.alignment = Alignment(
                vertical="center",
                horizontal="left",
                wrap_text=True
            )

            cell.border = Border(
                bottom=thin_grey
            )

        row[0].number_format = "@"
        row[1].number_format = "@"

        row[0].alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        row[3].alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        row[4].alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # ----------------------------------
    # Worksheet settings
    # ----------------------------------

    ws.freeze_panes = "A2"
    ws.sheet_view.showGridLines = False

    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_setup.orientation = "landscape"


# --------------------------------------------------
# 3. Export individual organized workbook
# --------------------------------------------------

def export_organized(file_path, result, inventory, filename_anomalies):

    data = result["data"]
    anomalies = result["anomalies"]
    company_records = result["company_records"]
    site_records = result["site_records"]
    file_anomalies = result["file_anomalies"]

    if data is None or data.empty:
        print("No records to export.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / (
        f"{file_path.stem}_organized.xlsx"
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        # ----------------------------------
        # 1. Organized sheet
        # ----------------------------------

        write_organized_sheet(writer, data, "Organized", "OrganizedTable")

        # ----------------------------------
        # 2. Anomalies sheet
        # ----------------------------------

        anomalies.to_excel(
            writer,
            sheet_name="Anomalies",
            index=False
        )

        anomaly_ws = writer.sheets["Anomalies"]

        style_header_row(anomaly_ws)

        anomaly_ws.column_dimensions["A"].width = 12
        anomaly_ws.column_dimensions["B"].width = 12
        anomaly_ws.column_dimensions["C"].width = 25
        anomaly_ws.column_dimensions["D"].width = 40
        anomaly_ws.column_dimensions["E"].width = 60

        add_choice_dropdown(anomaly_ws, "D", REASON_CHOICES + list(anomalies["異常原因"]))

        # Header filter on 異常原因 only
        anomaly_ws.auto_filter.ref = f"D1:D{max(anomaly_ws.max_row, 1)}"

        anomaly_ws.freeze_panes = "A2"

        # ----------------------------------
        # 3. File Inventory sheet
        # ----------------------------------

        write_table_sheet(writer, inventory, "File Inventory", [60, 22, 50, 100])

        # ----------------------------------
        # 4. Filename Anomalies sheet
        # ----------------------------------

        write_table_sheet(writer, filename_anomalies, "Filename Anomalies", [60, 22, 30, 100], filter_column="C")

        add_choice_dropdown(
            writer.sheets["Filename Anomalies"],
            "C",
            FILENAME_TYPE_CHOICES + list(filename_anomalies["異常類型"])
        )

        # ----------------------------------
        # 5. File Anomalies sheet
        # ----------------------------------

        write_table_sheet(writer, file_anomalies, "File Anomalies", [60, 22, 22, 40, 50, 100], filter_column="D")

        add_choice_dropdown(
            writer.sheets["File Anomalies"],
            "D",
            FILE_TYPE_CHOICES + list(file_anomalies["異常類型"])
        )

        # ----------------------------------
        # 6-7. Classification sheets
        # ----------------------------------

        write_organized_sheet(writer, company_records, "公司收文", "CompanyTable")
        write_organized_sheet(writer, site_records, "工地收文", "SiteTable")

    print(f"Exported: {output_file.name}")
    print(f"Records: {len(data)}")
    print(f"Anomalies: {len(anomalies)}")
    print(f"Inventory: {len(inventory)} file(s)")
    print(f"Filename anomalies: {len(filename_anomalies)}")
    print(f"File anomalies: {len(file_anomalies)}")
    print(f"公司收文: {len(company_records)}")
    print(f"工地收文: {len(site_records)}")


# --------------------------------------------------
# 4. Export all extracted results
# --------------------------------------------------

def process_results(results, parse_results=None, filename_anomalies=None):

    # No scan (no folders selected): the scan sheets are written with headers only
    inventory = build_inventory(parse_results) if parse_results is not None else pd.DataFrame(columns=INVENTORY_COLUMNS)

    if filename_anomalies is None:
        filename_anomalies = pd.DataFrame(columns=FILENAME_ANOMALY_COLUMNS)

    successful = 0
    failed = 0

    for result in results:

        file_path = Path(result["source"])

        # Same empty-table rule for File Anomalies when nothing was scanned
        if result["file_anomalies"] is None:
            result["file_anomalies"] = pd.DataFrame(columns=FILE_ANOMALY_COLUMNS)

        print(f"\nExporting: {file_path.name}")

        try:
            export_organized(file_path, result, inventory, filename_anomalies)

            successful += 1

        except Exception as error:

            print(f"FAILED: {error}")
            failed += 1

        print("-" * 45)

    print("\nEXPORT SUMMARY")
    print(f"Total: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
