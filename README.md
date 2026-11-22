# ClinicalFlow

A reproducible clinical research data management pipeline built with Python, SQLite and Nextflow DSL2.

ClinicalFlow demonstrates how synthetic clinical research data can be validated, standardised, integrated and stored in a relational database using an automated workflow.

## Key features

- Clinical data validation and quality checks.
- Standardisation of patient, laboratory and diagnosis datasets.
- SQLite database creation and data integration.
- Automated quality-control and cleaning reports.
- Nextflow DSL2 workflow orchestration.
- Unit and integration testing.

## Architecture

ClinicalFlow processes three synthetic CSV datasets through five Nextflow stages:

1. **VALIDATE** – checks input data quality.
2. **CHECK_QC** – stops processing if critical validation failures are detected.
3. **STANDARDIZE** – cleans and standardises the datasets.
4. **CREATE_DATABASE** – creates the SQLite database.
5. **LOAD_DATABASE** – loads the processed datasets.

See [Architecture documentation](docs/architecture.md) for the workflow diagram and database structure.

## Technology stack

- Python 3.11
- pandas and NumPy
- SQLite
- Nextflow DSL2
- pytest and Ruff
- Git and GitHub

## Input datasets

| Dataset | Fields |
|---|---|
| Patients | patient_id, age, sex, enrollment_date |
| Laboratory | patient_id, measurement_date, haemoglobin, creatinine, total_cholesterol |
| Diagnoses | patient_id, diagnosis_code, diagnosis_description, diagnosis_date |

## Installation

### Prerequisites

- Python 3.11
- Java
- Nextflow
- Git

Create and activate a Python environment:

```bash
git clone https://github.com/kashupp/ClinicalFlow.git
cd ClinicalFlow

python3 -m venv clinflow_env
source clinflow_env/bin/activate

pip install -r requirements.txt
pip install pytest ruff
```

Install Nextflow separately if it is not already available.

## Run the pipeline

```bash
nextflow run main.nf
```

Optional input and output directories:

```bash
nextflow run main.nf \
  --raw_dir data/raw \
  --outdir results/nextflow
```

## Pipeline outputs

The workflow generates:

- A validation report (`qc/qc_report.csv`)
- Three standardised datasets (`processed/`)
- A cleaning report (`cleaning/cleaning_report.csv`)
- A SQLite database (`database/clinicalflow.db`)

The demonstration dataset contains 1,000 patients, 1,979 laboratory records and 1,510 diagnosis records.

## Testing

Run the test suite:

```bash
python -m pytest -q
```

Check code quality:

```bash
ruff check scripts tests
ruff format --check scripts tests
```

## Documentation

- [Architecture](docs/architecture.md) — workflow stages and database structure.
- [Data dictionary](docs/data_dictionary.md) — dataset fields, data types and relationships.
