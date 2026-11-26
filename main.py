
from scripts.reader import process_all_excels
from scripts.combiner import process_results


# --------------------------------------------------
# Workflow
# --------------------------------------------------

def main():

    results = process_all_excels()

    if not results:
        return

    process_results(results)


if __name__ == "__main__":
    main()
