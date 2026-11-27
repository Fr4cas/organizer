
import re
from pathlib import Path

import pandas as pd

from scripts.validator import ID_PATTERN, SITE_ID_PATTERN


# --------------------------------------------------
# Configuration
# --------------------------------------------------

# Value used when no document number can be extracted
UNMATCHED_VALUE = ""

SEPARATORS = "-_ "

# Priority 2: 5+ digits, hyphen, 1-3 digits.
# A preceding letter, digit or hyphen is excluded so a Priority 3 number is not split.
PRIORITY_2_BODY = r"\d{5,}-\d{1,3}"
PRIORITY_3_BODY = r"\d{4}[A-Za-z]-\d{6}-\d{1,3}"

PRIORITY_2_SEARCH = re.compile(r"(?<![A-Za-z0-9-])" + PRIORITY_2_BODY + r"(?!\d)")
PRIORITY_3_SEARCH = re.compile(r"(?<![A-Za-z0-9])" + PRIORITY_3_BODY + r"(?!\d)")

PARENTHESIS_PATTERN = re.compile(r"\(([^()]*)\)")

MISSING_ID_ANOMALY = "單號擷取失敗"
FORMAT_ANOMALY = "單號格式錯誤"

FILENAME_ANOMALY_COLUMNS = [
    "檔名",
    "擷取單號",
    "異常類型",
    "路徑"
]


# --------------------------------------------------
# 1. Document number extraction
# --------------------------------------------------

def is_valid_number(text):

    return bool(
        re.fullmatch(PRIORITY_2_BODY, text)
        or re.fullmatch(PRIORITY_3_BODY, text)
    )


def find_document_number(stem):

    # Priority 1: valid number inside parentheses (first valid, left to right)
    for match in PARENTHESIS_PATTERN.finditer(stem):

        if is_valid_number(match.group(1)):
            return match.group(1), stem[match.end():]

    # Priority 2: general number-number pattern
    match = PRIORITY_2_SEARCH.search(stem)

    if match:
        return match.group(0), stem[match.end():]

    # Priority 3: specific alphanumeric format
    match = PRIORITY_3_SEARCH.search(stem)

    if match:
        return match.group(0), stem[match.end():]

    return None, None


# --------------------------------------------------
# 2. Filename parsing
# --------------------------------------------------

def parse_filename(filename):

    # Extension is removed here, so it never takes part in matching or the subject
    stem = Path(filename).stem

    number, remainder = find_document_number(stem)

    if number is None:
        return {
            "document_number": UNMATCHED_VALUE,
            "subject": UNMATCHED_VALUE
        }

    # The identifier is kept even when no description remains
    subject = remainder.lstrip(SEPARATORS)

    return {
        "document_number": number,
        "subject": subject
    }


# --------------------------------------------------
# 3. Filename identifier anomalies
# --------------------------------------------------

def check_extracted_identifier(number):

    if not number:
        return MISSING_ID_ANOMALY

    if not ID_PATTERN.fullmatch(number) and not SITE_ID_PATTERN.fullmatch(number):
        return FORMAT_ANOMALY

    return None


def find_filename_anomalies(parse_results):

    rows = [
        {
            "檔名": file["filename"],
            "擷取單號": file["document_number"],
            "異常類型": file["filename_anomaly"],
            "路徑": str(file["full_path"])
        }
        for file in parse_results["files"]
        if file["filename_anomaly"]
    ]

    return pd.DataFrame(rows, columns=FILENAME_ANOMALY_COLUMNS)


# --------------------------------------------------
# 4. Scan results enrichment
# --------------------------------------------------

def parse_scan_results(scan_results):

    files = []
    parsed_files = 0

    for file in scan_results["files"]:

        parsed = parse_filename(file["filename"])

        if parsed["document_number"]:
            parsed_files += 1

        # New record: scanner records themselves are not modified
        files.append({
            **file,
            **parsed,
            "filename_anomaly": check_extracted_identifier(parsed["document_number"])
        })

    return {
        "files": files,
        "total_files": len(files),
        "parsed_files": parsed_files,
        "unmatched_files": len(files) - parsed_files
    }


# --------------------------------------------------
# 5. Console summary
# --------------------------------------------------

def print_parse_summary(parse_results):

    anomaly_count = sum(1 for file in parse_results["files"] if file["filename_anomaly"])

    print("\nFILENAME PARSING SUMMARY")
    print("-" * 32)
    print(f"Total files processed: {parse_results['total_files']:,}")
    print(f"Identifier extracted: {parse_results['parsed_files']:,}")
    print(f"No identifier: {parse_results['unmatched_files']:,}")
    print(f"Filename anomalies: {anomaly_count:,}")
    print("-" * 32)
