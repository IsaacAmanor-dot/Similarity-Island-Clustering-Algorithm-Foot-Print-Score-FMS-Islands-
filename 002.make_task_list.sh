#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/000.config.sh"

printf "task_id\tcutoff\tlabel\tcase_name\tinput_file\n" > "${TASK_LIST}"

TASK_ID=0

for CUTOFF in "${FPS_CUTOFFS[@]}"; do

    TASK_ID=$((TASK_ID + 1))

    LABEL="$(cutoff_label "${CUTOFF}")"
    CASE_NAME="FPS_Island_${LABEL}"
    INPUT_FILE="${WORK_ROOT}/${CASE_NAME}.in"

    if [[ ! -s "${INPUT_FILE}" ]]; then
        echo "ERROR: Missing input file: ${INPUT_FILE}"
        exit 1
    fi

    printf "%s\t%s\t%s\t%s\t%s\n" \
        "${TASK_ID}" \
        "${CUTOFF}" \
        "${LABEL}" \
        "${CASE_NAME}" \
        "${INPUT_FILE}" \
        >> "${TASK_LIST}"

done

echo
echo "FPS task list created."
echo "Tasks: ${TASK_ID}"
echo "File:  ${TASK_LIST}"
echo

column -t -s $'\t' "${TASK_LIST}"
