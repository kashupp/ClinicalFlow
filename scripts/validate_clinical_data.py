
import argparse
import pandas as pd
from pathlib import Path

def main():

    # Define command-line arguments
    parser = argparse.ArgumentParser(
        description="Validate synthetic clinical research datasets"
    )

    parser.add_argument( "--patients", type=Path,
                        default=Path("data/raw/patients.csv")
                        )

    parser.add_argument("--laboratory", type=Path,
                        default=Path("data/raw/laboratory.csv")
                        )

    parser.add_argument( "--diagnoses", type=Path,
                        default=Path("data/raw/diagnoses.csv")
                        )

    parser.add_argument("--output", type=Path,
                        default=Path("results/qc/qc_report.csv")
                        )

    args = parser.parse_args()

    # Load datasets
    patients = pd.read_csv(args.patients)
    laboratory = pd.read_csv(args.laboratory)
    diagnoses = pd.read_csv(args.diagnoses)

    print("All clinical data loaded.")

    # Prepare QC report
    qc_results = []

    def add_check(dataset, check, status, details):
        qc_results.append({
            "dataset": dataset,
            "check": check,
            "status": status,
            "details": details
        })

    # Validate patient data
    missing_ids = patients["patient_id"].isna().sum()

    add_check("patients","Missing patient IDs",
                "PASS" if missing_ids == 0 else "FAIL",
                f"{missing_ids} missing IDs"
            )

    duplicate_ids = patients["patient_id"].duplicated().sum()

    add_check("patients", "Duplicate patient IDs",
                "PASS" if duplicate_ids == 0 else "FAIL",
                f"{duplicate_ids} duplicate IDs"
            )

    invalid_age = ( patients["age"].isna()
                    | ~patients["age"].between(0, 120)
                )

    add_check( "patients", "Age range",
                "PASS" if invalid_age.sum() == 0 else "FAIL",
                f"{invalid_age.sum()} invalid age records"
            )

    missing_sex = patients["sex"].isna().sum()

    add_check( "patients", "Missing sex values",
                "PASS" if missing_sex == 0 else "WARNING",
                f"{missing_sex} missing values"
            )

    # Validate laboratory data
    missing_lab_ids = laboratory["patient_id"].isna().sum()

    add_check( "laboratory", "Missing patient IDs",
                "PASS" if missing_lab_ids == 0 else "FAIL",
                f"{missing_lab_ids} missing IDs"
            )

    invalid_hb = ~laboratory["haemoglobin"].between(30, 220)

    invalid_creatinine = ~laboratory["creatinine"].between(5, 2000)

    invalid_cholesterol = ~laboratory["total_cholesterol"].between(0.1, 30)

    add_check( "laboratory", "Haemoglobin range",
                "PASS" if invalid_hb.sum() == 0 else "WARNING",
                f"{invalid_hb.sum()} unusual records"
            )

    add_check( "laboratory", "Creatinine range",
                "PASS" if invalid_creatinine.sum() == 0 else "WARNING",
                f"{invalid_creatinine.sum()} unusual records"
            )

    add_check( "laboratory", "Cholesterol range",
                "PASS" if invalid_cholesterol.sum() == 0 else "WARNING",
                f"{invalid_cholesterol.sum()} unusual records"
            )

    # Validate diagnosis data
    missing_diagnosis_ids = diagnoses["patient_id"].isna().sum()

    add_check( "diagnoses", "Missing patient IDs",
                "PASS" if missing_diagnosis_ids == 0 else "FAIL",
                f"{missing_diagnosis_ids} missing IDs"
            )

    # Check referential integrity
    known_patients = set(patients["patient_id"].dropna())

    unknown_lab_patients = ( set(laboratory["patient_id"].dropna()) - known_patients)

    unknown_diagnosis_patients = (set(diagnoses["patient_id"].dropna()) - known_patients)

    add_check( "laboratory", "Unknown patient references",
                "PASS" if len(unknown_lab_patients) == 0 else "FAIL",
                f"{len(unknown_lab_patients)} unknown patients"
            )

    add_check( "diagnoses", "Unknown patient references",
                "PASS" if len(unknown_diagnosis_patients) == 0 else "FAIL",
                f"{len(unknown_diagnosis_patients)} unknown patients"
            )

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
