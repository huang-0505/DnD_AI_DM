import argparse
import cleanser

def main(args=None):
    print("CLI Arguments:", args)

    if args.clean:
        cleanser.run_cleaning()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DnD Data Processor CLI - Clean dataset for Gemini fine-tuning"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean raw DnD dataset and upload cleaned files to GCS",
    )

    args = parser.parse_args()
    main(args)
