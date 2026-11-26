
import re
from pathlib import Path


# --------------------------------------------------
# Configuration
# --------------------------------------------------

# Value used when no document number or subject can be extracted
UNMATCHED_VALUE = ""

SEPARATORS = "-_ "

# Priority 2: 5+ digits, hyphen, 1-3 digits.
# A preceding hyphen is excluded so a Priority 3 number is not split.
PRIORITY_2_BODY = r"\d{5,}-\d{1,3}"
PRIORITY_3_BODY = r"\d{4}[A-Za-z]-\d{6}-\d{1,3}"

PRIORITY_2_SEARCH = re.compile(r"(?<![\d-])" + PRIORITY_2_BODY + r"(?!\d)")
PRIORITY_3_SEARCH = re.compile(r"(?<![A-Za-z0-9])" + PRIORITY_3_BODY + r"(?!\d)")

PARENTHESIS_PATTERN = re.compile(r"\(([^()]*)\)")


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

    subject = remainder.lstrip(SEPARATORS)

    # A number with no description is treated as unmatched
    if not subject:
        return {
            "document_number": UNMATCHED_VALUE,
            "subject": UNMATCHED_VALUE
        }

    return {
        "document_number": number,
        "subject": subject
    }


# --------------------------------------------------
# 3. Scan results enrichment
# --------------------------------------------------

def parse_scan_results(scan_results):

    files = []
    parsed_files = 0

    for file in scan_results["files"]:

        parsed = parse_filename(file["filename"])

        if parsed["document_number"] and parsed["subject"]:
            parsed_files += 1

        # New record: scanner records themselves are not modified
        files.append({
            **file,
            **parsed
        })

    return {
        "files": files,
        "total_files": len(files),
        "parsed_files": parsed_files,
        "unmatched_files": len(files) - parsed_files
    }


# --------------------------------------------------
# 4. Console summary
# --------------------------------------------------

def print_parse_summary(parse_results):

    print("\nFILENAME PARSING SUMMARY")
    print("-" * 32)
    print(f"Total files processed: {parse_results['total_files']:,}")
    print(f"Successfully parsed: {parse_results['parsed_files']:,}")
    print(f"Unmatched: {parse_results['unmatched_files']:,}")
    print("-" * 32)
