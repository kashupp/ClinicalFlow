import argparse
from pathlib import Path

import pandas as pd


def validate_patients(patients):
    qc_results = []

    def add_check(dataset, check, status, details):
        qc_results.append(
            {"dataset": dataset, "check": check, "status": status, "details": details}
        )

    # Missing patient IDs
    missing_ids = (
        patients["patient_id"].isna()
        | patients["patient_id"].astype("string").str.strip().eq("")
    ).sum()

    add_check(
        "patients",
        "Missing patient IDs",
        "PASS" if missing_ids == 0 else "FAIL",
        f"{missing_ids} missing IDs",
    )

    # Duplicate patient IDs
    normalized_ids = patients["patient_id"].astype("string").str.strip().str.upper()

    duplicate_ids = (
        normalized_ids[normalized_ids.notna() & normalized_ids.ne("")]
        .duplicated()
        .sum()
    )

    add_check(
        "patients",
        "Duplicate patient IDs",
        "PASS" if duplicate_ids == 0 else "FAIL",
        f"{duplicate_ids} duplicate IDs",
    )

    # Invalid age
    missing_age = patients["age"].isna()

    add_check(
        "patients",
        "Missing age values",
        "PASS" if missing_age.sum() == 0 else "WARNING",
        f"{missing_age.sum()} missing age records",
    )

    invalid_age = patients["age"].notna() & ~patients["age"].between(0, 120)

    add_check(
        "patients",
        "Age range",
        "PASS" if invalid_age.sum() == 0 else "FAIL",
        f"{invalid_age.sum()} invalid age records",
    )

    # Missing sex
    missing_sex = patients["sex"].isna().sum()

    add_check(
        "patients",
        "Missing sex values",
        "PASS" if missing_sex == 0 else "WARNING",
        f"{missing_sex} missing values",
    )

    valid_sex = ["Male", "Female"]

    invalid_sex = patients["sex"].notna() & ~patients["sex"].astype(
        "string"
    ).str.strip().str.title().isin(valid_sex)

    add_check(
        "patients",
        "Sex categories",
        "PASS" if invalid_sex.sum() == 0 else "WARNING",
        f"{invalid_sex.sum()} unexpected values",
    )
    return qc_results


def validate_laboratory(laboratory):
    qc_results = []

    def add_check(check, status, details):
        qc_results.append(
            {
                "dataset": "laboratory",
                "check": check,
                "status": status,
                "details": details,
            }
        )

    # Missing patient IDs
    missing_ids = (
        laboratory["patient_id"].isna()
        | laboratory["patient_id"].astype("string").str.strip().eq("")
    ).sum()

    add_check(
        "Missing patient IDs",
        "PASS" if missing_ids == 0 else "FAIL",
        f"{missing_ids} missing IDs",
    )

    # Missing measurements
    measurements = ["haemoglobin", "creatinine", "total_cholesterol"]
    missing_measurements = laboratory[measurements].isna().sum().sum()

    add_check(
        "Missing laboratory measurements",
        "PASS" if missing_measurements == 0 else "WARNING",
        f"{missing_measurements} missing values",
    )

    # Numeric ranges
    ranges = {
        "haemoglobin": (30, 220),
        "creatinine": (5, 2000),
        "total_cholesterol": (0.1, 30),
    }

    for column, (lower, upper) in ranges.items():
        invalid = (
            laboratory[column].notna() & ~laboratory[column].between(lower, upper)
        ).sum()

        add_check(
            f"{column} range",
            "PASS" if invalid == 0 else "WARNING",
            f"{invalid} unusual records",
        )

    # Duplicate laboratory records
    duplicate_records = laboratory.duplicated().sum()

    add_check(
        "Exact duplicate laboratory records",
        "PASS" if duplicate_records == 0 else "WARNING",
        f"{duplicate_records} exact duplicate records",
    )

    return qc_results


def validate_diagnoses(diagnoses):
    qc_results = []

    def add_check(check, status, details):
        qc_results.append(
            {
                "dataset": "diagnoses",
                "check": check,
                "status": status,
                "details": details,
            }
        )

    # Missing patient IDs
    missing_ids = (
        diagnoses["patient_id"].isna()
        | diagnoses["patient_id"].astype("string").str.strip().eq("")
    ).sum()

    add_check(
        "Missing patient IDs",
        "PASS" if missing_ids == 0 else "FAIL",
        f"{missing_ids} missing IDs",
    )

    # Missing diagnosis codes
    missing_codes = (
        diagnoses["diagnosis_code"].isna()
        | diagnoses["diagnosis_code"].astype("string").str.strip().eq("")
    ).sum()

    add_check(
        "Missing diagnosis codes",
        "PASS" if missing_codes == 0 else "WARNING",
        f"{missing_codes} missing codes",
    )

    # Missing diagnosis dates
    missing_dates = diagnoses["diagnosis_date"].isna().sum()

    add_check(
        "Missing diagnosis dates",
        "PASS" if missing_dates == 0 else "WARNING",
        f"{missing_dates} missing dates",
    )

    # Exact duplicate records
    duplicate_records = diagnoses.duplicated().sum()

    add_check(
        "Exact duplicate diagnosis records",
        "PASS" if duplicate_records == 0 else "WARNING",
        f"{duplicate_records} exact duplicate records",
    )

    return qc_results


def validate_dates(data, column, dataset):
    dates = pd.to_datetime(data[column], errors="coerce")

    missing = data[column].isna().sum()
    invalid = (data[column].notna() & dates.isna()).sum()

    return [
        {
            "dataset": dataset,
            "check": f"Missing {column}",
            "status": "PASS" if missing == 0 else "WARNING",
            "details": f"{missing} missing dates",
        },
        {
            "dataset": dataset,
            "check": f"Invalid {column}",
            "status": "PASS" if invalid == 0 else "WARNING",
            "details": f"{invalid} invalid dates",
        },
    ]


def validate_references(patients, laboratory, diagnoses):
    qc_results = []

    known_patients = set(patients["patient_id"].dropna())

    unknown_lab_patients = set(laboratory["patient_id"].dropna()) - known_patients

    unknown_diagnosis_patients = set(diagnoses["patient_id"].dropna()) - known_patients

    qc_results.append(
        {
            "dataset": "laboratory",
            "check": "Unknown patient references",
            "status": "PASS" if len(unknown_lab_patients) == 0 else "FAIL",
            "details": f"{len(unknown_lab_patients)} unknown patients",
        }
    )

    qc_results.append(
        {
            "dataset": "diagnoses",
            "check": "Unknown patient references",
            "status": "PASS" if len(unknown_diagnosis_patients) == 0 else "FAIL",
            "details": f"{len(unknown_diagnosis_patients)} unknown patients",
        }
    )

    return qc_results


def main():

    # Define command-line arguments
    parser = argparse.ArgumentParser(
        description="Validate synthetic clinical research datasets"
    )

    parser.add_argument("--patients", type=Path, default=Path("data/raw/patients.csv"))

    parser.add_argument(
        "--laboratory", type=Path, default=Path("data/raw/laboratory.csv")
    )

    parser.add_argument(
        "--diagnoses", type=Path, default=Path("data/raw/diagnoses.csv")
    )

    parser.add_argument("--output", type=Path, default=Path("results/qc/qc_report.csv"))

    args = parser.parse_args()

    # Load datasets
    patients = pd.read_csv(args.patients)
    laboratory = pd.read_csv(args.laboratory)
    diagnoses = pd.read_csv(args.diagnoses)

    print("All clinical data loaded.")

    # Prepare QC report
    qc_results = []

    def add_check(dataset, check, status, details):
        qc_results.append(
            {"dataset": dataset, "check": check, "status": status, "details": details}
        )

    # Dates
    qc_results.extend(validate_dates(patients, "enrollment_date", "patients"))

    qc_results.extend(validate_dates(laboratory, "measurement_date", "laboratory"))

    qc_results.extend(validate_dates(diagnoses, "diagnosis_date", "diagnoses"))
    # Validate patient data
    qc_results.extend(validate_patients(patients))

    # Validate laboratory data
    qc_results.extend(validate_laboratory(laboratory))

    # Validate diagnosis data
    qc_results.extend(validate_diagnoses(diagnoses))

    # Check referential integrity
    qc_results.extend(validate_references(patients, laboratory, diagnoses))
    # Generate QC report
    qc_report = pd.DataFrame(qc_results)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    qc_report.to_csv(args.output, index=False)

    # Print summary

    print("\n========== QUALITY CONTROL ==========")
    print(qc_report.to_string(index=False))

    print("\n========== SUMMARY ==========")
    print("Total checks:", len(qc_report))
    print("Passed:", (qc_report["status"] == "PASS").sum())
    print("Warnings:", (qc_report["status"] == "WARNING").sum())
    print("Failed:", (qc_report["status"] == "FAIL").sum())

    print(f"\nQC report saved to: {args.output}")


if __name__ == "__main__":
    main()
