
import os
from pathlib import Path

import tkinter as tk
from tkinter import filedialog


# --------------------------------------------------
# Configuration
# --------------------------------------------------

EXCLUDED_LABEL = "[EXCLUDED]"


# --------------------------------------------------
# 1. Main folder dialog
# --------------------------------------------------

def pick_folder():

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        selected = filedialog.askdirectory(
            title="Select a main folder"
        )
    finally:
        root.destroy()

    if not selected:
        return None

    return Path(selected).resolve()


# --------------------------------------------------
# 2. Subfolder discovery (immediate directories only)
# --------------------------------------------------

def list_immediate_subfolders(folder):

    try:
        with os.scandir(folder) as entries:
            return sorted(
                Path(entry.path)
                for entry in entries
                if entry.is_dir(follow_symlinks=False)
            )
    except OSError:
        return []


# --------------------------------------------------
# 3. Exclusion helpers
# --------------------------------------------------

def is_excluded(path, excluded_subfolders):

    return any(
        path == excluded or excluded in path.parents
        for excluded in excluded_subfolders
    )


def toggle_exclusion(path, excluded_subfolders):

    if path in excluded_subfolders:
        excluded_subfolders.remove(path)
        return

    # Excluding a folder makes any exclusions inside it redundant
    excluded_subfolders.difference_update(
        {excluded for excluded in excluded_subfolders if path in excluded.parents}
    )

    excluded_subfolders.add(path)


def clear_exclusions_within(folder, excluded_subfolders):

    excluded_subfolders.difference_update(
        {excluded for excluded in excluded_subfolders if excluded == folder or folder in excluded.parents}
    )


# --------------------------------------------------
# 4. Main folder list
# --------------------------------------------------

def add_main_folder(folder, selected_folders):

    for existing in selected_folders:

        if folder == existing:
            return f"Already selected: {folder}"

        if existing in folder.parents or folder in existing.parents:
            return f"Overlaps with a selected folder: {existing}"

    selected_folders.append(folder)

    return None


def remove_main_folder(folder, selected_folders, excluded_subfolders):

    selected_folders.remove(folder)

    excluded_subfolders.difference_update(
        {excluded for excluded in excluded_subfolders if excluded == folder or folder in excluded.parents}
    )


# --------------------------------------------------
# 5. Console display
# --------------------------------------------------

def print_main_menu(selected_folders, excluded_subfolders):

    print("\nSelected main folders:")

    if not selected_folders:
        print("  (none)")

    for number, folder in enumerate(selected_folders, start=1):

        excluded_count = sum(
            1 for excluded in excluded_subfolders if folder in excluded.parents
        )

        print(f"  {number}. {folder}  (excluded subfolders: {excluded_count})")


def print_exclusion_menu(main_folder, current, subfolders, excluded_subfolders):

    relative_parts = current.relative_to(main_folder).parts
    location = Path(main_folder.name, *relative_parts).as_posix()

    if current == main_folder:
        status = "Main folder (always included)"
    elif is_excluded(current, excluded_subfolders):
        status = EXCLUDED_LABEL
    else:
        status = "INCLUDED"

    print("\nEXCLUSION SETTINGS")
    print(f"Current folder: {location}/")
    print(f"Status: {status}")
    print("\nSubfolders:")

    if not subfolders:
        print("  (no subfolders)")

    width = max((len(path.name) for path in subfolders), default=0) + 1

    for number, path in enumerate(subfolders, start=1):

        label = f"{path.name}/".ljust(width + 1)
        marker = EXCLUDED_LABEL if is_excluded(path, excluded_subfolders) else ""

        print(f"[{number}] {label}{marker}".rstrip())

    print()

    if current != main_folder:
        print("[A] Exclude this folder")
        print("[I] Include this folder")
        print("[C] Clear exclusions here")
        print("[B] Back")
    else:
        print("[C] Clear exclusions here")

    print("[D] Done")


def print_selection(folder_config):

    print("\nFinal selection:")
    print("Selected main folders:")

    for folder in folder_config["selected_folders"]:
        print(f"  {folder}")

    print("Excluded subfolders:")

    if not folder_config["excluded_subfolders"]:
        print("  (none)")

    for path in folder_config["excluded_subfolders"]:
        print(f"  {path}")


# --------------------------------------------------
# 6. Interactive configuration
# --------------------------------------------------

def edit_exclusions(main_folder, excluded_subfolders):

    current = main_folder

    while True:

        subfolders = list_immediate_subfolders(current)

        print_exclusion_menu(main_folder, current, subfolders, excluded_subfolders)

        command = input(
            "Enter a folder number to open, or a command: "
        ).strip().upper()

        if command.isdigit():

            if 1 <= int(command) <= len(subfolders):
                current = subfolders[int(command) - 1]
            else:
                print("Invalid folder number.")

        elif command == "A" and current != main_folder:

            if current in excluded_subfolders:
                print("This folder is already excluded.")
            elif is_excluded(current, excluded_subfolders):
                print("This folder is inside an excluded folder. Include the parent folder to change it.")
            else:
                toggle_exclusion(current, excluded_subfolders)

        elif command == "I" and current != main_folder:

            if current in excluded_subfolders:
                excluded_subfolders.remove(current)
            elif is_excluded(current, excluded_subfolders):
                print("This folder is inside an excluded folder. Include the parent folder to change it.")
            else:
                print("This folder is already included.")

        elif command == "C":

            clear_exclusions_within(current, excluded_subfolders)

        elif command == "B" and current != main_folder:

            current = current.parent

        elif command == "D":

            return

        else:

            print("Invalid choice.")


def select_folders():

    selected_folders = []
    excluded_subfolders = set()

    while True:

        print_main_menu(selected_folders, excluded_subfolders)

        action = input(
            "\n[A] add folder  [R] remove folder  [E] edit exclusions  [D] done: "
        ).strip().upper()

        if action == "A":

            folder = pick_folder()

            if folder is None:
                print("No folder selected.")
                continue

            message = add_main_folder(folder, selected_folders)

            if message:
                print(message)

        elif action in ("R", "E"):

            verb = "remove" if action == "R" else "edit"

            number = input(f"Enter the folder number to {verb}: ").strip()

            if not number.isdigit() or not 1 <= int(number) <= len(selected_folders):
                print("Invalid folder number.")
                continue

            folder = selected_folders[int(number) - 1]

            if action == "R":
                remove_main_folder(folder, selected_folders, excluded_subfolders)
            else:
                edit_exclusions(folder, excluded_subfolders)

        elif action == "D":

            folder_config = {
                "selected_folders": list(selected_folders),
                "excluded_subfolders": sorted(excluded_subfolders)
            }

            if not selected_folders:
                return folder_config

            print_selection(folder_config)

            if input("\nConfirm these selections? [y/n]: ").strip().lower() == "y":
                return folder_config

        else:
            print("Invalid choice.")
