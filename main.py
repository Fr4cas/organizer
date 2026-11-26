
from scripts.reader import process_all_excels
from scripts.validator import find_anomalies
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

    process_results(results)


if __name__ == "__main__":
    main()
