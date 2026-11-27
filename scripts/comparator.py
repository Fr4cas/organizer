
from collections import Counter, defaultdict

import pandas as pd

from scripts.validator import ID_PATTERN, SITE_ID_PATTERN, REASON_SEPARATOR, FIRST_DATA_ROW
from scripts.reader import SOURCE_ROW_COLUMN


# --------------------------------------------------
# Configuration
# --------------------------------------------------

ID_COLUMN = "收文單號"
SUBJECT_COLUMN = "主旨"

# Filename subjects shorter than this are never used for subject matching
MIN_SUBJECT_LENGTH = 5

MISSING_FILE = "找不到對應檔案"
SUBJECT_CANDIDATE = "主旨比對成功，需人工確認"
MULTIPLE_SUBJECT = "多筆主旨符合，需人工確認"
NO_EXCEL_RECORD = "Excel 無對應紀錄"
NO_MATCH = "單號及主旨皆無法匹配"
DUPLICATE_FILE = "同單號多個檔案"

# Worksheet 2: Excel listing problems and possible physical filenames
EXCEL_ANOMALY_COLUMNS = [
    "原列",
    "整理列",
    "收文單號",
    "異常原因",
    "可能對應檔名"
]

# Worksheet 5: physical file comparison problems
FILE_ANOMALY_COLUMNS = [
    "檔名",
    "擷取單號",
    "對應 Excel 單號",
    "異常類型",
    "Excel 主旨",
    "路徑"
]


# --------------------------------------------------
# 1. Matching helpers
# --------------------------------------------------

def is_valid_identifier(value):

    return bool(ID_PATTERN.fullmatch(value) or SITE_ID_PATTERN.fullmatch(value))


def subject_contains(file_subject, excel_subject):

    # Simple containment: the filename subject must appear inside the Excel subject
    return len(file_subject) >= MIN_SUBJECT_LENGTH and file_subject in excel_subject


def read_excel_records(organized):

    return [
        {
            "id": str(row[ID_COLUMN]).strip(),
            "original_id": str(row[ID_COLUMN]),
            "subject": str(row[SUBJECT_COLUMN])
        }
        for _, row in organized.iterrows()
    ]


def join_pairs(records):

    # IDs and subjects are joined in the same order, so each pair stays aligned
    return (
        REASON_SEPARATOR.join(record["original_id"] for record in records),
        REASON_SEPARATOR.join(record["subject"] for record in records)
    )


def join_names(names):

    return REASON_SEPARATOR.join(
        dict.fromkeys(name for name in names if name)
    )


# --------------------------------------------------
# 2. Worksheet 5: file-side comparison
# --------------------------------------------------

def compare_excel_and_files(organized, file_records):

    excel_records = read_excel_records(organized)

    excel_by_id = defaultdict(list)

    for record in excel_records:

        # Blank IDs never match anything by identifier
        if record["id"]:
            excel_by_id[record["id"]].append(record)

    identifier_counts = Counter(
        file["document_number"]
        for file in file_records
        if file["document_number"]
    )

    rows = []

    for file in file_records:

        identifier = file["document_number"]

        # Files without an identifier are not compared (they stay in Filename Anomalies)
        if not identifier:
            continue

        matched = excel_by_id.get(identifier, [])

        reasons = []

        if matched:

            excel_side = matched

        else:

            candidates = [
                record for record in excel_records
                if subject_contains(file["subject"], record["subject"])
            ]

            excel_side = candidates

            if len(candidates) == 1:
                reasons.append(SUBJECT_CANDIDATE)

            elif len(candidates) > 1:
                reasons.append(MULTIPLE_SUBJECT)

            elif is_valid_identifier(identifier):
                reasons.append(NO_EXCEL_RECORD)

            else:
                reasons.append(NO_MATCH)

        if identifier_counts[identifier] > 1:
            reasons.append(DUPLICATE_FILE)

        if reasons:

            excel_ids, excel_subjects = join_pairs(excel_side)

            rows.append({
                "檔名": file["filename"],
                "擷取單號": identifier,
                "對應 Excel 單號": excel_ids,
                "異常類型": REASON_SEPARATOR.join(reasons),
                "Excel 主旨": excel_subjects,
                "路徑": str(file["full_path"])
            })

    return pd.DataFrame(rows, columns=FILE_ANOMALY_COLUMNS)


# --------------------------------------------------
# 3. Worksheet 2: Excel-side possible files
# --------------------------------------------------

def match_excel_to_files(excel_records, file_records):

    files_by_id = defaultdict(list)

    for file in file_records:

        if file["document_number"]:
            files_by_id[file["document_number"]].append(file)

    matches = []

    for record in excel_records:

        # Exact identifier matches come first
        exact = files_by_id.get(record["id"], []) if record["id"] else []

        if exact:

            files = exact

        else:

            files = [
                file for file in file_records
                if file["document_number"] and subject_contains(file["subject"], record["subject"])
            ]

        matches.append({
            "found": bool(files),
            "filenames": join_names(file["filename"] for file in files)
        })

    return matches


def build_excel_anomalies(validator_anomalies, organized, file_records):

    reasons_by_row = dict(
        zip(validator_anomalies["整理列"], validator_anomalies["異常原因"])
    )

    excel_records = read_excel_records(organized)

    # No scan (file_records is None): no file lookup, so no 找不到 and no possible filenames
    if file_records is not None:
        matches = match_excel_to_files(excel_records, file_records)
    else:
        matches = [None] * len(excel_records)

    rows = []

    for position, ((_, row), match) in enumerate(zip(organized.iterrows(), matches)):

        organized_row = position + FIRST_DATA_ROW

        reasons = [
            reason
            for reason in reasons_by_row.get(organized_row, "").split(REASON_SEPARATOR)
            if reason
        ]

        if match is not None and not match["found"]:
            reasons.append(MISSING_FILE)

        if reasons:

            rows.append({
                "原列": row[SOURCE_ROW_COLUMN],
                "整理列": organized_row,
                "收文單號": row[ID_COLUMN],
                "異常原因": REASON_SEPARATOR.join(reasons),
                "可能對應檔名": match["filenames"] if match is not None else ""
            })

    return pd.DataFrame(rows, columns=EXCEL_ANOMALY_COLUMNS)
