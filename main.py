
from scripts.reader import process_all_excels
from scripts.validator import find_anomalies
from scripts.folder_selector import select_folders
from scripts.file_scanner import scan_files, print_scan_summary
from scripts.combiner import process_results


# --------------------------------------------------
# Workflow
# --------------------------------------------------

def main():

    results = process_all_excels()

    if not results:
        return

    for result in results:

        result["anomalies"] = find_anomalies(result["data"])

    folder_config = select_folders()

    if folder_config["selected_folders"]:

        scan_results = scan_files(folder_config)

        print_scan_summary(folder_config, scan_results)

    else:

        print("\nNo main folders selected. Skipping file scan. Continuing with Excel export.")

    process_results(results)


if __name__ == "__main__":
    main()
