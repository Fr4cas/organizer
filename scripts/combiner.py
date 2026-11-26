
from pathlib import Path

import pandas as pd

from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side
)
from openpyxl.worksheet.table import Table, TableColumn, TableStyleInfo


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


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
# 1. Export individual organized workbook
# --------------------------------------------------

def export_organized(file_path, data, anomalies):

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

        data.to_excel(
            writer,
            sheet_name="Organized",
            index=False
        )

        ws = writer.sheets["Organized"]

        # ----------------------------------
        # Column headers
        # ----------------------------------

        style_header_row(ws)

        # ----------------------------------
        # Excel table
        # ----------------------------------

        last_row = ws.max_row

        table = Table(
            displayName="OrganizedTable",
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

        # ----------------------------------
        # Anomalies sheet
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
        anomaly_ws.column_dimensions["D"].width = 20

        anomaly_ws.freeze_panes = "A2"

    print(f"Exported: {output_file.name}")
    print(f"Records: {len(data)}")
    print(f"Anomalies: {len(anomalies)}")


# --------------------------------------------------
# 2. Export all extracted results
# --------------------------------------------------

def process_results(results):

    successful = 0
    failed = 0

    for result in results:

        file_path = Path(result["source"])

        print(f"\nExporting: {file_path.name}")

        try:
            export_organized(file_path, result["data"], result["anomalies"])

            successful += 1

        except Exception as error:

            print(f"FAILED: {error}")
            failed += 1

        print("-" * 45)

    print("\nEXPORT SUMMARY")
    print(f"Total: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
