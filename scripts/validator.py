
import re

import pandas as pd

from scripts.reader import SOURCE_ROW_COLUMN


# --------------------------------------------------
# Configuration
# --------------------------------------------------

# Organized sheet: header is row 1, first record is row 2
FIRST_DATA_ROW = 2

ID_COLUMN = "收文單號"

# YYMMDD-NN or YYMMDD-NNN (ASCII digits only)
ID_PATTERN = re.compile(r"[0-9]{6}-[0-9]{2,3}")

# Site receipt: NNNN + letter - YYMMDD - 1 to 3 digits (ASCII digits only)
SITE_ID_PATTERN = re.compile(r"[0-9]{4}[A-Za-z]-[0-9]{6}-[0-9]{1,3}")

ANOMALY_COLUMNS = [
    "原列",
    "整理列",
    "收文單號",
    "異常原因"
]

DUPLICATE_REASON = "單號重複"

# Full-width semicolon joins several anomaly reasons in one cell
REASON_SEPARATOR = "；"


# --------------------------------------------------
# 1. Check one record ID
# --------------------------------------------------

def check_id(value):

    value = str(value).strip()

    if not value:
        return "單號缺漏"

    if not ID_PATTERN.fullmatch(value) and not SITE_ID_PATTERN.fullmatch(value):
        return "格式錯誤"

    return None


# --------------------------------------------------
# 2. Find anomalies in extracted records
# --------------------------------------------------

def find_anomalies(data):

    anomalies = []

    # Duplicates are counted within this workbook; blank IDs are never duplicates
    ids = data[ID_COLUMN].astype(str).str.strip()
    id_counts = ids[ids != ""].value_counts()

    for organized_row, (_, record) in enumerate(
        data.iterrows(),
        start=FIRST_DATA_ROW
    ):

        value = str(record[ID_COLUMN]).strip()

        reasons = []

        format_reason = check_id(value)

        if format_reason:
            reasons.append(format_reason)

        if value and id_counts.get(value, 0) > 1:
            reasons.append(DUPLICATE_REASON)

        if reasons:

            anomalies.append({
                "原列": record[SOURCE_ROW_COLUMN],
                "整理列": organized_row,
                "收文單號": record[ID_COLUMN],
                "異常原因": REASON_SEPARATOR.join(reasons)
            })

    return pd.DataFrame(anomalies, columns=ANOMALY_COLUMNS)
