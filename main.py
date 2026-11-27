
from scripts.reader import process_all_excels
from scripts.validator import find_anomalies
from scripts.classifier import classify_records
from scripts.folder_selector import select_folders
from scripts.file_scanner import scan_files, print_scan_summary
from scripts.filename_parser import parse_scan_results, print_parse_summary, find_filename_anomalies
from scripts.comparator import compare_excel_and_files, build_excel_anomalies
from scripts.combiner import process_results


# --------------------------------------------------
# Workflow
# --------------------------------------------------

def main():

    results = process_all_excels()

    if not results:
        return

    for result in results:

        result["validator_anomalies"] = find_anomalies(result["data"])

        result["company_records"], result["site_records"] = classify_records(result["data"])

        result["file_anomalies"] = None

    folder_config = select_folders()

    parse_results = None
    filename_anomalies = None
    file_records = None

    if folder_config["selected_folders"]:

        scan_results = scan_files(folder_config)

        print_scan_summary(folder_config, scan_results)

        parse_results = parse_scan_results(scan_results)

        print_parse_summary(parse_results)

        filename_anomalies = find_filename_anomalies(parse_results)

        file_records = parse_results["files"]

        for result in results:

            result["file_anomalies"] = compare_excel_and_files(result["data"], file_records)

    else:

        print("\nNo main folders selected. Skipping file scan. Continuing with Excel export.")

    # Built after the scan: adds 找不到對應檔案 and possible filenames (none without a scan)
    for result in results:

        result["anomalies"] = build_excel_anomalies(
            result["validator_anomalies"],
            result["data"],
            file_records
        )

    process_results(results, parse_results, filename_anomalies)


if __name__ == "__main__":
    main()
