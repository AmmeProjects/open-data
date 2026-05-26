import os
import sys
import argparse
import glob
import yaml

from src.tariffs.model import TariffDocument


DEFAULT_OUTPUT_PATH = os.path.join("data", "tariffs", "pt", "master.json")


def main():
    parser = argparse.ArgumentParser(
        description="Compile multiple tariff YAML files into a master JSON file."
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="*",
        default=[os.path.join("data", "tariffs")],
        help="Files or directories to compile (default: data/tariffs)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path for the output master JSON file (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()

    files_to_compile = set()
    for path in args.input:
        if os.path.isfile(path):
            if path.endswith((".yaml", ".yml")):
                files_to_compile.add(path)
        elif os.path.isdir(path):
            tariffs_path = os.path.join(path, "**", "*.yaml")
            for f in glob.glob(tariffs_path, recursive=True):
                files_to_compile.add(f)

    # Exclude template.yaml from compilation as it's a structural reference
    files = sorted(
        [f for f in files_to_compile if "template.yaml" not in os.path.basename(f)]
    )

    if not files:
        print("No YAML files found to compile.")
        sys.exit(1)

    master_providers = []
    errors = False

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Load and validate using Pydantic from validate_tariffs
            doc = TariffDocument.model_validate(data)
            master_providers.extend(doc.providers)

            print(f"[OK] Read {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to process {file_path}: {e}")
            errors = True

    if errors:
        print("\nCompilation aborted due to validation or parsing errors.")
        sys.exit(1)

    # Create the master document
    master_doc = TariffDocument(providers=master_providers)

    # Ensure output directory exists
    output_dir = os.path.dirname(os.path.abspath(args.output))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Dump the master document to JSON
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(master_doc.model_dump_json(indent=2))

    print(f"\nSuccessfully compiled {len(files)} files into {args.output}")


if __name__ == "__main__":
    main()
