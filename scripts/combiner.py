
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
# 1. Export individual organized workbook
# --------------------------------------------------

def export_organized(file_path, data, anomalies, inventory):

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

        # ----------------------------------
        # File inventory sheet
        # ----------------------------------

        if inventory is not None:

            inventory.to_excel(
                writer,
                sheet_name="File Inventory",
                index=False
            )

            inventory_ws = writer.sheets["File Inventory"]

            style_header_row(inventory_ws)

            # Keep filenames and paths as text (e.g. "=..." must not become a formula)
            for row in inventory_ws.iter_rows(min_row=2):

                for cell in row:

                    if isinstance(cell.value, str) and cell.value.startswith("="):
                        cell.data_type = "s"

            inventory_ws.column_dimensions["A"].width = 60
            inventory_ws.column_dimensions["B"].width = 22
            inventory_ws.column_dimensions["C"].width = 50
            inventory_ws.column_dimensions["D"].width = 100

            inventory_ws.freeze_panes = "A2"
            inventory_ws.auto_filter.ref = f"A1:D{inventory_ws.max_row}"

    print(f"Exported: {output_file.name}")
    print(f"Records: {len(data)}")
    print(f"Anomalies: {len(anomalies)}")

    if inventory is not None:
        print(f"Inventory: {len(inventory)} file(s)")


# --------------------------------------------------
# 2. Export all extracted results
# --------------------------------------------------

def process_results(results, parse_results=None):

    # No scan (no folders selected) means no inventory sheet, same as before
    inventory = build_inventory(parse_results) if parse_results is not None else None

    successful = 0
    failed = 0

    for result in results:

        file_path = Path(result["source"])

        print(f"\nExporting: {file_path.name}")

        try:
            export_organized(file_path, result["data"], result["anomalies"], inventory)

            successful += 1

        except Exception as error:

            print(f"FAILED: {error}")
            failed += 1

        print("-" * 45)

    print("\nEXPORT SUMMARY")
    print(f"Total: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
