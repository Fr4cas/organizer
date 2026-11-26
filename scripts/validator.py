
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

ANOMALY_COLUMNS = [
    "原列",
    "整理列",
    "收文單號",
    "異常原因"
]


# --------------------------------------------------
# 1. Check one record ID
# --------------------------------------------------

def check_id(value):

    value = str(value).strip()

    if not value:
        return "單號缺漏"

    if not ID_PATTERN.fullmatch(value):
        return "格式錯誤"

    return None


# --------------------------------------------------
# 2. Find anomalies in extracted records
# --------------------------------------------------

def find_anomalies(data):

    anomalies = []

    for organized_row, (_, record) in enumerate(
        data.iterrows(),
        start=FIRST_DATA_ROW
    ):

        reason = check_id(record[ID_COLUMN])

        if reason:

            anomalies.append({
                "原列": record[SOURCE_ROW_COLUMN],
                "整理列": organized_row,
                "收文單號": record[ID_COLUMN],
                "異常原因": reason
            })

    return pd.DataFrame(anomalies, columns=ANOMALY_COLUMNS)
