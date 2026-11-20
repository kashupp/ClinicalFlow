
nextflow.enable.dsl = 2

params.raw_dir = params.raw_dir ?: "${projectDir}/data/raw"
params.outdir = params.outdir ?: "${projectDir}/results/nextflow"


process VALIDATE {
    tag "Clinical data validation"

    publishDir "${params.outdir}/qc", mode: 'copy'

    input:
    path patients
    path laboratory
    path diagnoses
    path validate_script

    output:
    path 'qc_report.csv', emit: report

    script:
    """
    python "${validate_script}" \
        --patients "${patients}" \
        --laboratory "${laboratory}" \
        --diagnoses "${diagnoses}" \
        --output qc_report.csv
    """
}


process CHECK_QC {
    tag "Check validation results"

    input:
    path qc_report

    output:
    path 'qc_pass.txt', emit: pass

    script:
    """
    python - "${qc_report}" <<'PY'
import csv
import sys

report = sys.argv[1]

with open(report, newline="") as handle:
    rows = list(csv.DictReader(handle))

failed = [
    row for row in rows
    if row.get("status", "").strip().upper() == "FAIL"
]

if failed:
    print("VALIDATION FAILED:")
    for row in failed:
        print(
            f"{row['dataset']}: {row['check']} - {row['details']}"
        )
    sys.exit(1)

print("Validation passed. No FAIL results found.")

with open("qc_pass.txt", "w") as handle:
    handle.write("Validation passed.\\n")
PY
    """
}


process STANDARDIZE {
    tag "Clinical data standardisation"

    publishDir "${params.outdir}", mode: 'copy'

    input:
    path patients
    path laboratory
    path diagnoses
    path qc_pass
    path standardize_script

    output:
    path 'processed/patients_clean.csv', emit: patients_clean
    path 'processed/laboratory_clean.csv', emit: laboratory_clean
    path 'processed/diagnoses_clean.csv', emit: diagnoses_clean
    path 'cleaning/cleaning_report.csv', emit: cleaning_report

    script:
    """
    mkdir -p processed cleaning

    python "${standardize_script}" \
        --input-dir . \
        --output-dir processed \
        --log-dir cleaning
    """
}


process CREATE_DATABASE {
    tag "Create SQLite database"

    input:
    path create_script

    output:
    path 'clinicalflow.db', emit: database

    script:
    """
    python "${create_script}" --database clinicalflow.db
    """
}


process LOAD_DATABASE {
    tag "Load SQLite database"

    stageInMode 'copy'

    publishDir "${params.outdir}/database", mode: 'copy'

    input:
    path database
    path patients
    path laboratory
    path diagnoses
    path load_script

    output:
    path 'clinicalflow.db', emit: database

    script:
    """
    python "${load_script}" \
        --database clinicalflow.db \
        --patients "${patients}" \
        --laboratory "${laboratory}" \
        --diagnoses "${diagnoses}"
    """
}


workflow {

    raw_patients = Channel.fromPath(
        "${params.raw_dir}/patients.csv",
        checkIfExists: true
    )

    raw_laboratory = Channel.fromPath(
        "${params.raw_dir}/laboratory.csv",
        checkIfExists: true
    )

    raw_diagnoses = Channel.fromPath(
        "${params.raw_dir}/diagnoses.csv",
        checkIfExists: true
    )

    validate_script = Channel.fromPath(
        "${projectDir}/scripts/validate_clinical_data.py",
        checkIfExists: true
    )

    standardize_script = Channel.fromPath(
        "${projectDir}/scripts/standardize_clinical_data.py",
        checkIfExists: true
    )

    create_script = Channel.fromPath(
        "${projectDir}/scripts/create_database.py",
        checkIfExists: true
    )

    load_script = Channel.fromPath(
        "${projectDir}/scripts/load_database.py",
        checkIfExists: true
    )

    VALIDATE(
        raw_patients,
        raw_laboratory,
        raw_diagnoses,
        validate_script
    )

    CHECK_QC(VALIDATE.out.report)

    STANDARDIZE(
        raw_patients,
        raw_laboratory,
        raw_diagnoses,
        CHECK_QC.out.pass,
        standardize_script
    )

    CREATE_DATABASE(create_script)

    LOAD_DATABASE(
        CREATE_DATABASE.out.database,
        STANDARDIZE.out.patients_clean,
        STANDARDIZE.out.laboratory_clean,
        STANDARDIZE.out.diagnoses_clean,
        load_script
    )
}
