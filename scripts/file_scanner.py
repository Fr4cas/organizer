
import os
from pathlib import Path


# --------------------------------------------------
# 1. Skip rules
# --------------------------------------------------

def is_skipped_directory(path, excluded_subfolders):

    if path in excluded_subfolders:
        return True

    # Never follow links or junctions (they can point back into the tree)
    return path.is_symlink() or path.is_junction()


# --------------------------------------------------
# 2. Scan selected main folders
# --------------------------------------------------

def scan_files(folder_config):

    excluded_subfolders = set(folder_config["excluded_subfolders"])

    files = []
    inaccessible_folders = []
    seen_paths = set()

    def record_inaccessible(error):

        inaccessible_folders.append(Path(error.filename))

    for main_folder in folder_config["selected_folders"]:

        for root, dirnames, filenames in os.walk(
            main_folder,
            onerror=record_inaccessible
        ):

            dirnames[:] = [
                name for name in dirnames
                if not is_skipped_directory(Path(root, name), excluded_subfolders)
            ]

            for filename in filenames:

                full_path = Path(root, filename)

                # Overlapping selections must not record a file twice
                if full_path in seen_paths:
                    continue

                seen_paths.add(full_path)

                files.append({
                    "filename": filename,
                    "full_path": full_path
                })

    return {
        "files": files,
        "inaccessible_folders": inaccessible_folders,
        "total_files": len(files)
    }


# --------------------------------------------------
# 3. Console summary
# --------------------------------------------------

def print_scan_summary(folder_config, scan_results):

    print("\nFILE SCANNING SUMMARY")
    print("-" * 32)
    print(f"Selected main folders: {len(folder_config['selected_folders'])}")
    print(f"Excluded subfolders: {len(folder_config['excluded_subfolders'])}")
    print(f"Total files discovered: {scan_results['total_files']:,}")
    print(f"Inaccessible folders: {len(scan_results['inaccessible_folders'])}")
    print("-" * 32)
    print("Scanning completed.")

    if scan_results["inaccessible_folders"]:

        print("\nInaccessible folders (not scanned):")

        for folder in scan_results["inaccessible_folders"]:
            print(f"  {folder}")
