import re
from pathlib import Path

import pandas as pd

# Project directories
RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
LOG_DIR = Path("results/cleaning")


# Audit logging
def record_action(cleaning_log, dataset, action, affected_rows, details):
    cleaning_log.append(
        {
            "dataset": dataset,
            "action": action,
            "affected_rows": int(affected_rows),
            "details": details,
        }
    )


# Standardize column names
def clean_column_names(df, dataset, cleaning_log):
    original_columns = df.columns.tolist()

    df.columns = [
        re.sub(
            r"_+",
            "_",
            re.sub(r"[^a-zA-Z0-9]+", "_", col.strip().lower()),
        ).strip("_")
        for col in df.columns
    ]

    changed = sum(old != new for old, new in zip(original_columns, df.columns))

    record_action(
        cleaning_log,
        dataset,
        "Column name standardization",
        changed,
        "Converted column names to lowercase snake_case",
    )

    if df.columns.duplicated().any():
        raise ValueError(f"{dataset}: duplicate column names after standardization")

    return df


# Standardize missing values
def clean_missing_values(df, dataset, cleaning_log):
    missing_tokens = ["", "NA", "N/A", "NULL", "None", "unknown"]
    changed = 0

    for col in df.select_dtypes(include=["object", "string"]).columns:
        values = df[col].astype("string").str.strip()
        mask = values.str.upper().isin([token.upper() for token in missing_tokens])

        changed += int(mask.sum())
        df[col] = values.mask(mask, pd.NA)

    record_action(
        cleaning_log,
        dataset,
        "Missing value standardization",
        changed,
        "Converted recognized missing-value tokens to NA",
    )

    return df


# Standardize patient identifiers
def clean_identifiers(df, dataset, cleaning_log):
    if "patient_id" not in df.columns:
        raise ValueError(f"{dataset}: patient_id column is missing")

    original = df["patient_id"].copy()

    df["patient_id"] = df["patient_id"].astype("string").str.strip().str.upper()

    changed = int((original.fillna("") != df["patient_id"].fillna("")).sum())

    record_action(
        cleaning_log,
        dataset,
        "Patient identifier standardization",
        changed,
        "Removed surrounding whitespace and converted IDs to uppercase",
    )

    return df


# Standardize dates
def standardize_dates(df, columns, dataset, cleaning_log):
    for col in columns:
        if col not in df.columns:
            raise ValueError(f"{dataset}: required date column '{col}' is missing")

        original = df[col].copy()
        parsed = pd.to_datetime(original, errors="coerce")

        invalid = original.notna() & parsed.isna()

        record_action(
            cleaning_log,
            dataset,
            f"Date conversion: {col}",
            int(parsed.notna().sum()),
            f"{int(invalid.sum())} invalid non-missing dates",
        )

        df[col] = parsed.dt.strftime("%Y-%m-%d")

    return df


# Standardize sex categories
def standardize_sex(df, cleaning_log):
    if "sex" not in df.columns:
        return df

    original = df["sex"].copy()

    df["sex"] = (
        df["sex"]
        .astype("string")
        .str.strip()
        .str.lower()
        .replace(
            {
                "f": "Female",
                "female": "Female",
                "m": "Male",
                "male": "Male",
            }
        )
    )

    changed = int((original.fillna("") != df["sex"].fillna("")).sum())

    record_action(
        cleaning_log,
        "patients",
        "Sex category standardization",
        changed,
        "Standardized recognized sex categories",
    )

    return df


# Convert numeric variables
def convert_numeric(df, columns, dataset, cleaning_log):
    for col in columns:
        if col not in df.columns:
            raise ValueError(f"{dataset}: required numeric column '{col}' is missing")

        original = df[col].copy()
        converted = pd.to_numeric(original, errors="coerce")

        invalid = original.notna() & converted.isna()

        record_action(
            cleaning_log,
            dataset,
            f"Numeric conversion: {col}",
            int(converted.notna().sum()),
            f"{int(invalid.sum())} invalid numeric values",
        )

        df[col] = converted

    return df


# Standardize diagnosis fields
def standardize_diagnoses(diagnoses):
    required_columns = ["diagnosis_code", "diagnosis_description"]

    for col in required_columns:
        if col not in diagnoses.columns:
            raise ValueError(f"diagnoses: required column '{col}' is missing")

    diagnoses["diagnosis_code"] = (
        diagnoses["diagnosis_code"].astype("string").str.strip().str.upper()
    )

    diagnoses["diagnosis_description"] = (
        diagnoses["diagnosis_description"].astype("string").str.strip()
    )

    return diagnoses


# Load raw datasets
def load_datasets():
    datasets = {
        "patients": pd.read_csv(
            RAW_DIR / "patients.csv",
            dtype={"patient_id": "string"},
        ),
        "laboratory": pd.read_csv(
            RAW_DIR / "laboratory.csv",
            dtype={"patient_id": "string"},
        ),
        "diagnoses": pd.read_csv(
            RAW_DIR / "diagnoses.csv",
            dtype={"patient_id": "string"},
        ),
    }

    return datasets


# Process all datasets
def process_datasets(datasets, cleaning_log):
    patients = clean_column_names(datasets["patients"].copy(), "patients", cleaning_log)
    patients = clean_missing_values(patients, "patients", cleaning_log)
    patients = clean_identifiers(patients, "patients", cleaning_log)
    patients = standardize_sex(patients, cleaning_log)
    patients = convert_numeric(patients, ["age"], "patients", cleaning_log)
    patients = standardize_dates(
        patients, ["enrollment_date"], "patients", cleaning_log
    )

    laboratory = clean_column_names(
        datasets["laboratory"].copy(), "laboratory", cleaning_log
    )
    laboratory = clean_missing_values(laboratory, "laboratory", cleaning_log)
    laboratory = clean_identifiers(laboratory, "laboratory", cleaning_log)
    laboratory = convert_numeric(
        laboratory,
        ["haemoglobin", "creatinine", "total_cholesterol"],
        "laboratory",
        cleaning_log,
    )
    laboratory = standardize_dates(
        laboratory, ["measurement_date"], "laboratory", cleaning_log
    )

    diagnoses = clean_column_names(
        datasets["diagnoses"].copy(), "diagnoses", cleaning_log
    )
    diagnoses = clean_missing_values(diagnoses, "diagnoses", cleaning_log)
    diagnoses = clean_identifiers(diagnoses, "diagnoses", cleaning_log)
    diagnoses = standardize_diagnoses(diagnoses)
    diagnoses = standardize_dates(
        diagnoses, ["diagnosis_date"], "diagnoses", cleaning_log
    )

    processed = {
        "patients": patients,
        "laboratory": laboratory,
        "diagnoses": diagnoses,
    }

    return processed


# Assess duplicate records
def assess_duplicates(processed, cleaning_log):
    for name, df in processed.items():
        duplicate_count = int(df.duplicated().sum())

        record_action(
            cleaning_log,
            name,
            "Duplicate record assessment",
            duplicate_count,
            "Exact duplicate rows identified; retained for review",
        )


# Save processed datasets and audit report
def save_outputs(processed, cleaning_log):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for name, df in processed.items():
        df.to_csv(OUTPUT_DIR / f"{name}_clean.csv", index=False)

    cleaning_report = pd.DataFrame(cleaning_log)

    cleaning_report.to_csv(
        LOG_DIR / "cleaning_report.csv",
        index=False,
    )


# Main execution
def main():
    print("Loading clinical datasets...")

    datasets = load_datasets()

    cleaning_log = []

    processed = process_datasets(datasets, cleaning_log)

    assess_duplicates(processed, cleaning_log)

    save_outputs(processed, cleaning_log)

    print("\n===================================")
    print("CLINICAL DATA STANDARDIZATION")
    print("===================================")

    for name, df in processed.items():
        print(f"{name.capitalize()}: {len(df)}")

    print("\nOutput files generated:")
    for name in processed:
        print(OUTPUT_DIR / f"{name}_clean.csv")

    print("\nCleaning report generated:")
    print(LOG_DIR / "cleaning_report.csv")

    print("\nStandardization completed successfully.")


if __name__ == "__main__":
    main()
