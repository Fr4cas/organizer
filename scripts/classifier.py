
from scripts.validator import SITE_ID_PATTERN


# --------------------------------------------------
# Configuration
# --------------------------------------------------

ID_COLUMN = "收文單號"

# Site-format identifiers starting with this code are company receipts
COMPANY_CODE = "2300A"


# --------------------------------------------------
# 1. Classify one record ID
# --------------------------------------------------

def is_site_receipt(value):

    value = str(value).strip()

    if not SITE_ID_PATTERN.fullmatch(value):
        return False

    return value.split("-", 1)[0].upper() != COMPANY_CODE


# --------------------------------------------------
# 2. Split records into company and site receipts
# --------------------------------------------------

def classify_records(data):

    is_site = data[ID_COLUMN].apply(is_site_receipt)

    company_records = data[~is_site].copy()
    site_records = data[is_site].copy()

    return company_records, site_records
