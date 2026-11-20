import argparse
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_PATH = DATA_DIR / "clinicalflow.db"

DATASETS = {
    "patients": PROCESSED_DIR / "patients_clean.csv",
    "laboratory": PROCESSED_DIR / "laboratory_clean.csv",
    "diagnoses": PROCESSED_DIR / "diagnoses_clean.csv",
}


def load_csv(connection, table_name, file_path):
    df = pd.read_csv(file_path)

    df.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False,
    )
    return len(df)


def load_database(database_path=DATABASE_PATH, datasets=DATASETS):
    connection = sqlite3.connect(database_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            for table_name, file_path in datasets.items():
                if not file_path.exists():
                    raise FileNotFoundError(f"Dataset not found: {file_path}")

                count = load_csv(
                    connection,
                    table_name,
                    file_path,
                )

                print(f"{table_name}: {count} records loaded")

        print("\nDatabase loading completed successfully.")

    except Exception:
        print("\nDatabase loading failed. Transaction rolled back.")
        raise

    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="Load cleaned clinical datasets into SQLite"
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DATABASE_PATH,
    )
    parser.add_argument(
        "--patients",
        type=Path,
        default=DATASETS["patients"],
    )
    parser.add_argument(
        "--laboratory",
        type=Path,
        default=DATASETS["laboratory"],
    )
    parser.add_argument(
        "--diagnoses",
        type=Path,
        default=DATASETS["diagnoses"],
    )

    args = parser.parse_args()

    datasets = {
        "patients": args.patients,
        "laboratory": args.laboratory,
        "diagnoses": args.diagnoses,
    }

    load_database(args.database, datasets)


if __name__ == "__main__":
    main()
