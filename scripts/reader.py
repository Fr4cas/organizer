
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"

REQUIRED_COLUMNS = [
    "收文單號",
    "來文字號",
    "主旨",
    "收文部門"
]

SUPPORTED_EXTENSIONS = {
    ".xlsx",
    ".xlsm",
    ".xls"
}


# --------------------------------------------------
# 1. Discover Excel workbooks
# --------------------------------------------------

def discover_excel_files():

    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True)
        print(f"Created input directory: {INPUT_DIR}")

    excel_files = sorted(
        file for file in INPUT_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in SUPPORTED_EXTENSIONS
        and not file.name.startswith("~$")
    )

    return excel_files


# --------------------------------------------------
# 2. Detect header row
# --------------------------------------------------

def detect_header_row(file_path):

    preview = pd.read_excel(
        file_path,
        sheet_name=0,
        header=None,
        nrows=3,
        dtype=str,
        keep_default_na=False
    )

    for index, row in preview.iterrows():

        values = [
            str(value).strip()
            for value in row.tolist()
        ]

        if all(
            column in values
            for column in REQUIRED_COLUMNS
        ):
            return index

    raise ValueError(
        "Required headers not found in the first three rows."
    )


# --------------------------------------------------
# 3. Read individual workbook
# --------------------------------------------------

def read_excel(file_path):

    header_row = detect_header_row(file_path)

    df = pd.read_excel(
        file_path,
        sheet_name=0,
        header=header_row,
        dtype=str,
        keep_default_na=False
    )

    df.columns = df.columns.astype(str).str.strip()

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    df = df[REQUIRED_COLUMNS].copy()

    # Remove completely empty records
    df = df[
        df[REQUIRED_COLUMNS].apply(
            lambda row: any(
                str(value).strip()
                for value in row
            ),
            axis=1
        )
    ]

    return df


# --------------------------------------------------
# 4. Process all workbooks
# --------------------------------------------------

def process_all_excels():

    excel_files = discover_excel_files()

    if not excel_files:
        print("No Excel workbooks found in input directory.")
        return []

    results = []

    print(f"\nFound {len(excel_files)} Excel workbook(s).")
    print("=" * 55)

    for file_path in excel_files:

        print(f"\nProcessing: {file_path.name}")

        try:
            data = read_excel(file_path)

            results.append({
                "source": file_path.name,
                "data": data
            })

            print(f"Successfully extracted {len(data)} records.")

        except Exception as error:

            print(f"FAILED: {error}")

    print("\n" + "=" * 55)
    print("PROCESSING SUMMARY")
    print("=" * 55)

    print(f"Total workbooks found: {len(excel_files)}")
    print(f"Successfully processed: {len(results)}")
    print(f"Failed: {len(excel_files) - len(results)}")

    total_records = sum(
        len(result["data"])
        for result in results
    )

    print(f"Total records extracted: {total_records}")

    return results
