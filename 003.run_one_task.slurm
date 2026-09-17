#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 TASK_ID"
    exit 1
fi

TASK_ID="$1"

if [[ -n "${FPS_WORK_ROOT:-}" ]]; then
    SCRIPT_DIR="${FPS_WORK_ROOT}"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

source "${SCRIPT_DIR}/000.config.sh"

TASK_LINE=$(awk -F '\t' -v ID="${TASK_ID}" '
NR > 1 && $1 == ID {
    print
    exit
}
' "${TASK_LIST}")

if [[ -z "${TASK_LINE}" ]]; then
    echo "ERROR: Task ${TASK_ID} not found."
    exit 1
fi

IFS=$'\t' read -r \
    TASK_ID \
    CUTOFF \
    LABEL \
    CASE_NAME \
    INPUT_FILE \
    <<< "${TASK_LINE}"

OUTPUT_FILE="${WORK_ROOT}/${CASE_NAME}.out"
SUMMARY_FILE="${WORK_ROOT}/${CASE_NAME}_summary.out"

SUCCESS_FILE="${WORK_ROOT}/.${CASE_NAME}.success"
FAILED_FILE="${WORK_ROOT}/.${CASE_NAME}.failed"

if [[ -f "${SUCCESS_FILE}" ]] \
    && [[ -s "${OUTPUT_FILE}" ]] \
    && grep -q "Similarity Island clustering complete" "${OUTPUT_FILE}" 2>/dev/null; then

    echo "Already complete: ${CASE_NAME}"
    exit 0
fi

rm -f "${SUCCESS_FILE}" "${FAILED_FILE}"

echo
echo "FPS Similarity Island calculation"
echo
echo "Task ID: ${TASK_ID}"
echo "Cutoff:  ${CUTOFF}"
echo "Case:    ${CASE_NAME}"
echo "Input:   ${INPUT_FILE}"
echo "Output:  ${OUTPUT_FILE}"
echo
echo "Started: $(date)"
echo

set +e

"${DOCK_BIN}" \
    -i "${INPUT_FILE}" \
    -o "${OUTPUT_FILE}"

DOCK_EXIT=$?

set -e

if [[ ${DOCK_EXIT} -eq 0 ]] \
    && [[ -s "${OUTPUT_FILE}" ]] \
    && [[ -s "${SUMMARY_FILE}" ]] \
    && grep -q "Similarity Island clustering complete" "${OUTPUT_FILE}"; then

    touch "${SUCCESS_FILE}"

    echo
    echo "SUCCESS: ${CASE_NAME}"
    echo "Finished: $(date)"
    echo

    exit 0
fi

touch "${FAILED_FILE}"

echo
echo "FAILED: ${CASE_NAME}"
echo "DOCK exit code: ${DOCK_EXIT}"
echo "Finished: $(date)"
echo

exit 1
