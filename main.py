"""
Main module for the open-data package.
Three primary functions are defined here:
- Extract data from Spain NAP (static)
- Extract data from Portugal NAP (static)
- Extract data from Mobie tariffs (static)
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Run data collection scripts for open-data package.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available scripts:
  spain         - Extract data from Spain NAP (static locations)
  portugal      - Extract data from Portugal NAP (static locations)
  mobie-tariffs - Extract Mobie tariff data (Portugal)
  all           - Run all data collection scripts
        """,
    )

    parser.add_argument(
        "script",
        choices=["spain", "portugal", "mobie-tariffs", "all"],
        help="The data collection script to run",
    )

    args = parser.parse_args()

    scripts_to_run = []

    if args.script == "all":
        scripts_to_run = ["spain", "portugal", "mobie-tariffs"]
    else:
        scripts_to_run = [args.script]

    for script in scripts_to_run:
        print(f"\n{'=' * 60}")
        print(f"Running: {script}")
        print(f"{'=' * 60}\n")

        try:
            if script == "spain":
                from scripts.naps.spain import update_locations

                update_locations()
                print("✓ Spain NAP data extraction completed successfully")

            elif script == "portugal":
                from scripts.naps.portugal import update_locations

                update_locations()
                print("✓ Portugal NAP data extraction completed successfully")

            elif script == "mobie-tariffs":
                import subprocess

                subprocess.run(
                    [sys.executable, "scripts/custom/mobie_tariffs.py"], check=True
                )
                print("✓ Mobie tariffs extraction completed successfully")

        except Exception as e:
            print(f"✗ Error running {script}: {str(e)}", file=sys.stderr)
            sys.exit(1)

    print(f"\n{'=' * 60}")
    print("All requested scripts completed successfully!")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
