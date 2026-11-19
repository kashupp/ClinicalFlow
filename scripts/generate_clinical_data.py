from pathlib import Path

import numpy as np
import pandas as pd

# Set variable values
RANDOM_SEED = 41
N_PATIENTS = 1000

np.random.seed(RANDOM_SEED)

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Generate dummay patient details

# Patient IDs
patient_ids = [f"PAT{i:04d}" for i in range(1, N_PATIENTS + 1)]

patients = pd.DataFrame(
    {
        "patient_id": patient_ids,
        "age": np.random.randint(30, 90, N_PATIENTS),
        "sex": np.random.choice(["Female", "Male"], N_PATIENTS),
        "enrollment_date": pd.to_datetime(
            np.random.choice(pd.date_range("2024-01-01", "2026-11-01"), N_PATIENTS)
        ),
    }
)

# Generate laboratorytest values

lab_records = []

for patient_id in patient_ids:
    n_measurements = np.random.randint(1, 4)
    for _ in range(n_measurements):
        lab_records.append(
            {
                "patient_id": patient_id,
                "measurement_date": pd.Timestamp("2025-01-01")
                + pd.Timedelta(days=int(np.random.randint(0, 365))),
                "haemoglobin": round(np.random.normal(135, 15), 1),
                "creatinine": round(np.random.normal(85, 20), 1),
                "total_cholesterol": round(np.random.normal(5.2, 1.0), 2),
            }
        )

laboratory = pd.DataFrame(lab_records)

# 4. Generate diagnosis IDs and records

diagnosis_options = [
    ("I10", "Essential hypertension"),
    ("I25.1", "Atherosclerotic heart disease"),
    ("I50.9", "Heart failure"),
    ("E78.5", "Dyslipidaemia"),
]

diagnosis_records = []

for patient_id in patient_ids:
    n_diagnoses = np.random.randint(1, 3)
    selected_diagnoses = np.random.choice(
        len(diagnosis_options), n_diagnoses, replace=False
    )
    for diagnosis_index in selected_diagnoses:
        code, description = diagnosis_options[diagnosis_index]
        diagnosis_records.append(
            {
                "patient_id": patient_id,
                "diagnosis_code": code,
                "diagnosis_description": description,
                "diagnosis_date": pd.Timestamp("2025-01-01")
                + pd.Timedelta(days=int(np.random.randint(0, 365))),
            }
        )

diagnoses = pd.DataFrame(diagnosis_records)

# Save synthetic data

patients.to_csv(OUTPUT_DIR / "patients.csv", index=False)

laboratory.to_csv(OUTPUT_DIR / "laboratory.csv", index=False)

diagnoses.to_csv(OUTPUT_DIR / "diagnoses.csv", index=False)

print("Synthetic clinical datasets generated successfully!")

print(f"Patients: {len(patients)}")
print(f"Laboratory records: {len(laboratory)}")
print(f"Diagnosis records: {len(diagnoses)}")
