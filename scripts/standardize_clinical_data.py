
import pandas as pd
import re
from pathlib import Path

# Set variable values
RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
LOG_DIR = Path("results/cleaning")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

cleaning_log = []

# AUDIT LOGGING
def record_action(dataset, action, affected_rows, details):
    cleaning_log.append({
            "dataset": dataset,
            "action": action,
            "affected_rows": int(affected_rows),
            "details": details
        })

# Standardize column names
def clean_column_names(df, dataset):

    original_columns = df.columns.tolist()
    df.columns = [
        re.sub( r"_+", "_",
            re.sub( r"[^a-zA-Z0-9]+", "_", col.strip().lower())
                ).strip("_")
        for col in df.columns
    ]

    changed = sum( old != new
                    for old, new in zip(original_columns, df.columns)
                )

    record_action( dataset, "Column name standardization", 
                             changed,
                            "Converted column names to lowercase snake_case"
                )

    if df.columns.duplicated().any():
            raise ValueError(
                f"{dataset}: duplicate column names after standardization"
            )
    return df


# Standardize missing values 
def clean_missing_values(df, dataset):

    missing_tokens = [ "", "NA", "N/A", "NULL", "None", "unknown"]

    changed = 0

    for col in df.select_dtypes( include=["object", "string"]).columns:

        values = df[col].astype("string").str.strip()

        mask = values.str.upper().isin(
                            [token.upper() for token in missing_tokens]
            )

        changed += int(mask.sum())

        df[col] = values.mask(mask, pd.NA)

    record_action( dataset, "Missing value standardization",
                            changed,
                            "Converted recognized missing-value tokens to NA"
                )

    return df

# Standardize identifiers
def clean_identifiers(df, dataset):

    if "patient_id" not in df.columns:
                raise ValueError(
                            f"{dataset}: patient_id column is missing"
                    )

    original = df["patient_id"].copy()

    df["patient_id"] = ( df["patient_id"]
                            .astype("string")
                            .str.strip()
                            .str.upper()
                        )

    changed = int( (original.fillna("") !=
                    df["patient_id"].fillna("")).sum()
                )

    record_action(dataset, "Patient identifier standardization",
                            changed,
                            "Removed surrounding whitespace and converted IDs to uppercase"
                )
    return df


# Standardize dates
def standardize_dates(df, columns, dataset):

    for col in columns:
        original = df[col].copy()
        parsed = pd.to_datetime( original, errors="coerce")
        invalid = ( original.notna() & parsed.isna())

        record_action( dataset, f"Date conversion: {col}",
                                int(parsed.notna().sum()),
                                f"{int(invalid.sum())} invalid non-missing dates"
                    )
        df[col] = parsed.dt.strftime("%Y-%m-%d")
    return df


# Standardize categorical features
def standardize_sex(df):
    if "sex" not in df.columns:
        return df

    original = df["sex"].copy()

    df["sex"] = ( df["sex"]
                    .astype("string")
                    .str.strip()
                    .str.lower()
                    .replace({
                        "f": "Female",
                        "female": "Female",
                        "m": "Male",
                        "male": "Male"
                    })
                )

    changed = int( (original.fillna("") !=
                    df["sex"].fillna("")).sum()
                )

    record_action( "patients", "Sex category standardization",
                                changed,
                                "Standardized recognized sex categories"
                )
    return df

# Convert numeric variables 
def convert_numeric(df, columns, dataset):
    
    for col in columns:
        original = df[col].copy()
        converted = pd.to_numeric( original, errors="coerce"
        )

        invalid = (
            original.notna()
            & converted.isna()
        )

        record_action(
            dataset,
            f"Numeric conversion: {col}",
            int(converted.notna().sum()),
            f"{int(invalid.sum())} invalid numeric values")
        df[col] = converted
    return df

# Load all data 
datasets = { "patients": pd.read_csv(
                        RAW_DIR / "patients.csv",
                        dtype={"patient_id": "string"}),
            "laboratory": pd.read_csv(
                        RAW_DIR / "laboratory.csv",
                        dtype={"patient_id": "string"}),
            "diagnoses": pd.read_csv( 
                        RAW_DIR / "diagnoses.csv",
                        dtype={"patient_id": "string"})
            }


# Clean/QC'd patients
patients = datasets["patients"].copy()
patients = clean_column_names(patients, "patients")
patients = clean_missing_values(patients, "patients")
patients = clean_identifiers(patients, "patients")
patients = standardize_sex(patients)

patients = convert_numeric( patients, ["age"], "patients")

patients = standardize_dates( patients, ["enrollment_date"], "patients")

# Clean/QC'd laboratory data
laboratory = datasets["laboratory"].copy()
laboratory = clean_column_names( laboratory, "laboratory")
laboratory = clean_missing_values(laboratory, "laboratory")
laboratory = clean_identifiers( laboratory, "laboratory")

laboratory = convert_numeric(
    laboratory,
    [
        "haemoglobin",
        "creatinine",
        "total_cholesterol"
    ],
    "laboratory"
)
laboratory = standardize_dates(
    laboratory,
    ["measurement_date"],
    "laboratory"
)

# Clean/QC'd diagnosis data
diagnoses = datasets["diagnoses"].copy()

diagnoses = clean_column_names( diagnoses, "diagnoses")
diagnoses = clean_missing_values( diagnoses, "diagnoses")
diagnoses = clean_identifiers(diagnoses, "diagnoses")
diagnoses["diagnosis_code"] = ( diagnoses["diagnosis_code"]
                                .astype("string")
                                .str.strip()
                                .str.upper()
                            )
diagnoses["diagnosis_description"] = ( diagnoses["diagnosis_description"]
                                        .astype("string")
                                        .str.strip()
                                    )
diagnoses = standardize_dates( diagnoses, ["diagnosis_date"], "diagnoses")

# Record the duplicate information
for name, df in { "patients": patients,
                 "laboratory": laboratory,
                "diagnoses": diagnoses}.items():
    duplicate_count = int( df.duplicated().sum())
    
    record_action( name, "Duplicate record assessment",
                         duplicate_count,
                        "Exact duplicate rows identified; retained for review"
                )


# Save all clean data
patients.to_csv( OUTPUT_DIR / "patients_clean.csv", index=False)

laboratory.to_csv( OUTPUT_DIR / "laboratory_clean.csv", index=False)

diagnoses.to_csv( OUTPUT_DIR / "diagnoses_clean.csv", index=False)


# Export and save cleaning audit log

cleaning_report = pd.DataFrame(cleaning_log)

cleaning_report.to_csv( LOG_DIR / "cleaning_report.csv", index=False)

# Print summary
print("\n===================================")
print("CLINICAL DATA STANDARDIZATION")
print("===================================")

print("Patients:", len(patients))
print("Laboratory:", len(laboratory))
print("Diagnoses:", len(diagnoses))

print("\nOutput files generated:")
print(OUTPUT_DIR / "patients_clean.csv")
print(OUTPUT_DIR / "laboratory_clean.csv")
print(OUTPUT_DIR / "diagnoses_clean.csv")

print("\nCleaning report generated:")
print(LOG_DIR / "cleaning_report.csv")

print("\nStandardization completed successfully.")
