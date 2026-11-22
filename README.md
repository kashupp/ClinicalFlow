# ClinicalFlow

A reproducible clinical research data management pipeline built with Python, SQLite, Nextflow DSL2 and Docker.

ClinicalFlow demonstrates how synthetic clinical research data can be validated, standardised, integrated and stored in a relational database through an automated workflow.

## Key features

- Clinical data validation and quality checks.
- Standardisation of patient, laboratory and diagnosis datasets.
- SQLite database creation and data integration.
- Automated quality-control and cleaning reports.
- Nextflow DSL2 workflow orchestration.
- Docker-based execution for a consistent Python environment.
- Unit and integration testing.
- Automated code quality checks using GitHub Actions.

## Architecture

ClinicalFlow processes three synthetic CSV datasets through five Nextflow stages:

1. **VALIDATE** – validates the input datasets.
2. **CHECK_QC** – checks validation results and stops the workflow if failures are detected.
3. **STANDARDIZE** – standardises clinical data and generates a cleaning report.
4. **CREATE_DATABASE** – creates the SQLite database.
5. **LOAD_DATABASE** – loads the standardised datasets into the database.

See [docs/architecture.md](docs/architecture.md) for the workflow architecture and database structure.

## Technology stack

| Component | Technology |
|---|---|
| Programming language | Python 3.11 |
| Data processing | pandas 2.1.4, NumPy 1.26.4 |
| Relational database | SQLite |
| Workflow management | Nextflow DSL2 |
| Containerisation | Docker |
| Testing | pytest |
| Code quality | Ruff |
| CI | GitHub Actions |

## Input datasets

ClinicalFlow uses three synthetic CSV datasets.

| Dataset | Main fields |
|---|---|
| Patients | patient_id, age, sex, enrollment_date |
| Laboratory | patient_id, measurement_date, haemoglobin, creatinine, total_cholesterol |
| Diagnoses | patient_id, diagnosis_code, diagnosis_description, diagnosis_date |

See [docs/data_dictionary.md](docs/data_dictionary.md) for field descriptions, database data types and relationships.

## Installation

### Prerequisites

- Python 3.11
- Java 21
- Nextflow
- Docker Desktop
- Git

### Clone the repository

```bash
git clone https://github.com/kashupp/ClinicalFlow.git
cd ClinicalFlow
```

### Set up the Python environment

```bash
python3.11 -m venv clinflow_env
source clinflow_env/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install pytest ruff
```

## Run the pipeline with Docker

Docker provides the Python environment used by the Nextflow processes.

### Build the Docker image

```bash
docker build -t clinicalflow:1.0 .
```

### Run the pipeline

Make sure Docker Desktop is running.

```bash
nextflow run main.nf -with-docker clinicalflow:1.0 \
  --raw_dir data/raw \
  --outdir results/docker
```

Nextflow and Java run on the host system, while the five pipeline processes execute inside the Docker container.

## Pipeline outputs

The workflow generates:

| Output | Description |
|---|---|
| qc/qc_report.csv | Data validation results |
| processed/patients_clean.csv | Standardised patient dataset |
| processed/laboratory_clean.csv | Standardised laboratory dataset |
| processed/diagnoses_clean.csv | Standardised diagnosis dataset |
| cleaning/cleaning_report.csv | Record of data cleaning actions |
| database/clinicalflow.db | Integrated SQLite database |

The synthetic dataset contains:

- 1,000 patients
- 1,979 laboratory records
- 1,510 diagnosis records

## Testing

Run all unit and integration tests:

```bash
python -m pytest -v
```

Run Ruff linting:

```bash
ruff check scripts tests
```

Check code formatting:

```bash
ruff format --check scripts tests
```

The GitHub Actions workflow automatically runs code quality checks and tests on pushes to the main and feature branches and on pull requests targeting main.

The integration test runs the complete Nextflow pipeline and verifies the expected outputs, quality-control results and database record counts.

## Documentation

- [Architecture](docs/architecture.md) – workflow stages, execution architecture and database relationships.
- [Data dictionary](docs/data_dictionary.md) – dataset fields, database data types and relationships.
