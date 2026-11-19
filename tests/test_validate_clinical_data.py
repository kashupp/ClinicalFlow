import pandas as pd

from scripts.validate_clinical_data import (
    validate_dates,
    validate_diagnoses,
    validate_laboratory,
    validate_patients,
    validate_references,
)


# Patient checks
def test_valid_patient_data():
    patients = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0002"],
            "age": [45, 67],
            "sex": ["Male", "Female"],
        }
    )

    results = validate_patients(patients)

    assert len(results) == 6
    assert all(result["status"] == "PASS" for result in results)


def test_missing_patient_id():
    patients = pd.DataFrame(
        {"patient_id": [None, "PAT0002"], "age": [45, 67], "sex": ["Male", "Female"]}
    )

    results = validate_patients(patients)

    missing_id_check = next(
        result for result in results if result["check"] == "Missing patient IDs"
    )

    assert missing_id_check["status"] == "FAIL"


def test_duplicate_patient_ids():
    patients = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0001"],
            "age": [45, 67],
            "sex": ["Male", "Female"],
        }
    )

    results = validate_patients(patients)

    duplicate_check = next(
        result for result in results if result["check"] == "Duplicate patient IDs"
    )

    assert duplicate_check["status"] == "FAIL"


def test_invalid_patient_age():
    patients = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0002"],
            "age": [45, 150],
            "sex": ["Male", "Female"],
        }
    )

    results = validate_patients(patients)

    age_check = next(result for result in results if result["check"] == "Age range")

    assert age_check["status"] == "FAIL"


def test_blank_patient_id():
    patients = pd.DataFrame(
        {"patient_id": ["", "PAT0002"], "age": [45, 67], "sex": ["Male", "Female"]}
    )

    results = validate_patients(patients)

    missing_id_check = next(
        result for result in results if result["check"] == "Missing patient IDs"
    )

    assert missing_id_check["status"] == "FAIL"


def test_missing_age():
    patients = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0002"],
            "age": [45, None],
            "sex": ["Male", "Female"],
        }
    )

    results = validate_patients(patients)

    age_check = next(
        result for result in results if result["check"] == "Missing age values"
    )

    assert age_check["status"] == "WARNING"


def test_duplicate_patient_ids_with_different_formatting():
    patients = pd.DataFrame(
        {
            "patient_id": ["PAT0001", " pat0001 "],
            "age": [45, 67],
            "sex": ["Male", "Female"],
        }
    )

    results = validate_patients(patients)

    duplicate_check = next(
        result for result in results if result["check"] == "Duplicate patient IDs"
    )

    assert duplicate_check["status"] == "FAIL"
    assert duplicate_check["details"] == "1 duplicate IDs"


def test_invalid_sex_category():
    patients = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0002"],
            "age": [45, 67],
            "sex": ["Male", "Other"],
        }
    )

    results = validate_patients(patients)

    sex_check = next(
        result for result in results if result["check"] == "Sex categories"
    )

    assert sex_check["status"] == "WARNING"
    assert sex_check["details"] == "1 unexpected values"


# Laboratory checks
def test_valid_laboratory_data():
    laboratory = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0001"],
            "measurement_date": ["2025-01-01", "2025-01-02"],
            "haemoglobin": [130, 140],
            "creatinine": [80, 90],
            "total_cholesterol": [4.5, 5.0],
        }
    )

    results = validate_laboratory(laboratory)

    assert len(results) == 6
    assert all(result["status"] == "PASS" for result in results)


def test_exact_duplicate_laboratory_records():
    laboratory = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0001"],
            "measurement_date": ["2025-01-01", "2025-01-01"],
            "haemoglobin": [130, 130],
            "creatinine": [80, 80],
            "total_cholesterol": [4.5, 4.5],
        }
    )

    results = validate_laboratory(laboratory)

    duplicate_check = next(
        result
        for result in results
        if result["check"] == "Exact duplicate laboratory records"
    )

    assert duplicate_check["status"] == "WARNING"
    assert duplicate_check["details"] == "1 exact duplicate records"


# Diagnosis checks
def test_valid_diagnosis_data():
    diagnoses = pd.DataFrame(
        {
            "patient_id": ["PAT0001"],
            "diagnosis_code": ["C90.0"],
            "diagnosis_description": ["Multiple myeloma"],
            "diagnosis_date": ["2025-01-01"],
        }
    )

    results = validate_diagnoses(diagnoses)

    assert len(results) == 4
    assert all(result["status"] == "PASS" for result in results)


def test_missing_diagnosis_code():
    diagnoses = pd.DataFrame(
        {
            "patient_id": ["PAT0001"],
            "diagnosis_code": [None],
            "diagnosis_description": ["Multiple myeloma"],
            "diagnosis_date": ["2025-01-01"],
        }
    )

    results = validate_diagnoses(diagnoses)

    code_check = next(
        result for result in results if result["check"] == "Missing diagnosis codes"
    )

    assert code_check["status"] == "WARNING"


def test_missing_diagnosis_date():
    diagnoses = pd.DataFrame(
        {
            "patient_id": ["PAT0001"],
            "diagnosis_code": ["C90.0"],
            "diagnosis_description": ["Multiple myeloma"],
            "diagnosis_date": [None],
        }
    )

    results = validate_diagnoses(diagnoses)

    date_check = next(
        result for result in results if result["check"] == "Missing diagnosis dates"
    )

    assert date_check["status"] == "WARNING"


def test_exact_duplicate_diagnosis_records():
    diagnoses = pd.DataFrame(
        {
            "patient_id": ["PAT0001", "PAT0001"],
            "diagnosis_code": ["C90.0", "C90.0"],
            "diagnosis_description": ["Multiple myeloma", "Multiple myeloma"],
            "diagnosis_date": ["2025-01-01", "2025-01-01"],
        }
    )

    results = validate_diagnoses(diagnoses)

    duplicate_check = next(
        result
        for result in results
        if result["check"] == "Exact duplicate diagnosis records"
    )

    assert duplicate_check["status"] == "WARNING"
    assert duplicate_check["details"] == "1 exact duplicate records"


# Date chekcks
def test_valid_dates():
    data = pd.DataFrame({"date": ["2025-01-01", "2025-02-15"]})

    results = validate_dates(data, "date", "test")

    assert all(result["status"] == "PASS" for result in results)


def test_invalid_date():
    data = pd.DataFrame({"date": ["2025-01-01", "not-a-date"]})

    results = validate_dates(data, "date", "test")

    invalid_check = next(
        result for result in results if result["check"] == "Invalid date"
    )

    assert invalid_check["status"] == "WARNING"
    assert invalid_check["details"] == "1 invalid dates"


# Key integrety tests
def test_unknown_laboratory_patient_reference():
    patients = pd.DataFrame({"patient_id": ["PAT0001"]})

    laboratory = pd.DataFrame({"patient_id": ["PAT0001", "PAT9999"]})

    diagnoses = pd.DataFrame({"patient_id": ["PAT0001"]})

    results = validate_references(patients, laboratory, diagnoses)

    lab_check = next(result for result in results if result["dataset"] == "laboratory")

    assert lab_check["status"] == "FAIL"
    assert lab_check["details"] == "1 unknown patients"


def test_unknown_diagnosis_patient_reference():
    patients = pd.DataFrame({"patient_id": ["PAT0001"]})

    laboratory = pd.DataFrame({"patient_id": ["PAT0001"]})

    diagnoses = pd.DataFrame({"patient_id": ["PAT0001", "PAT9999"]})

    results = validate_references(patients, laboratory, diagnoses)

    diagnosis_check = next(
        result for result in results if result["dataset"] == "diagnoses"
    )

    assert diagnosis_check["status"] == "FAIL"
    assert diagnosis_check["details"] == "1 unknown patients"
