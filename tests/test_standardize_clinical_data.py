import pandas as pd
import pytest

from scripts.standardize_clinical_data import (
    clean_column_names,
    clean_identifiers,
    clean_missing_values,
    convert_numeric,
    standardize_dates,
    standardize_diagnoses,
    standardize_sex,
)


def test_clean_column_names():
    df = pd.DataFrame(
        {
            "Patient ID": ["P001"],
            "Enrollment-Date": ["2025-01-01"],
        }
    )

    result = clean_column_names(df, "patients", [])

    assert list(result.columns) == ["patient_id", "enrollment_date"]


def test_clean_column_names_rejects_duplicates():
    df = pd.DataFrame([[1, 2]], columns=["Patient ID", "patient-id"])

    with pytest.raises(ValueError):
        clean_column_names(df, "patients", [])


def test_clean_missing_values():
    df = pd.DataFrame({"value": ["", "NA", "N/A", "NULL", "None", "unknown", "valid"]})

    result = clean_missing_values(df, "patients", [])

    assert result["value"].iloc[:6].isna().all()
    assert result["value"].iloc[6] == "valid"


def test_clean_identifiers():
    df = pd.DataFrame({"patient_id": [" pat0001 ", "Pat0002", None]})

    result = clean_identifiers(df, "patients", [])

    assert result["patient_id"].iloc[0] == "PAT0001"
    assert result["patient_id"].iloc[1] == "PAT0002"
    assert pd.isna(result["patient_id"].iloc[2])


def test_clean_identifiers_requires_patient_id():
    df = pd.DataFrame({"other_id": ["P001"]})

    with pytest.raises(ValueError):
        clean_identifiers(df, "patients", [])


def test_standardize_dates():
    df = pd.DataFrame(
        {
            "collection_date": [
                "2025-01-02",
                "not-a-date",
                None,
            ]
        }
    )
    cleaning_log = []

    result = standardize_dates(df, ["collection_date"], "laboratory", cleaning_log)

    assert result["collection_date"].iloc[0] == "2025-01-02"
    assert pd.isna(result["collection_date"].iloc[1])
    assert pd.isna(result["collection_date"].iloc[2])


def test_standardize_dates_requires_column():
    df = pd.DataFrame({"other_date": ["2025-01-01"]})

    with pytest.raises(ValueError):
        standardize_dates(df, ["collection_date"], "laboratory", [])


def test_standardize_sex():
    df = pd.DataFrame({"sex": ["m", "F", "male", "Female", " other ", None]})

    result = standardize_sex(df, [])

    assert result["sex"].iloc[0] == "Male"
    assert result["sex"].iloc[1] == "Female"
    assert result["sex"].iloc[2] == "Male"
    assert result["sex"].iloc[3] == "Female"
    assert result["sex"].iloc[4] == "other"
    assert pd.isna(result["sex"].iloc[5])


def test_convert_numeric():
    df = pd.DataFrame({"haemoglobin": ["130", "bad-value", None]})

    result = convert_numeric(df, ["haemoglobin"], "laboratory", [])

    assert result["haemoglobin"].iloc[0] == 130.0
    assert pd.isna(result["haemoglobin"].iloc[1])
    assert pd.isna(result["haemoglobin"].iloc[2])


def test_convert_numeric_requires_column():
    df = pd.DataFrame({"other_value": [10]})

    with pytest.raises(ValueError):
        convert_numeric(df, ["haemoglobin"], "laboratory", [])


def test_standardize_diagnoses():
    df = pd.DataFrame(
        {
            "diagnosis_code": [" c90.0 "],
            "diagnosis_description": [" Multiple myeloma "],
        }
    )

    result = standardize_diagnoses(df)

    assert result["diagnosis_code"].iloc[0] == "C90.0"
    assert result["diagnosis_description"].iloc[0] == "Multiple myeloma"


def test_standardize_diagnoses_requires_columns():
    df = pd.DataFrame({"diagnosis_code": ["C90.0"]})

    with pytest.raises(ValueError):
        standardize_diagnoses(df)
