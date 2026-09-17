#!/bin/bash
#SBATCH --job-name=FPS_Islands
#SBATCH --partition=rn-long-40core
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --time=2-00:00:00
#SBATCH --output=FPS_slurm_%j.out

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${SCRIPT_DIR}/000.config.sh"

cd "${WORK_ROOT}"

if [[ ! -s "${TASK_LIST}" ]]; then
    echo "ERROR: Missing task list: ${TASK_LIST}"
    echo "Run 002.make_task_list.sh first."
    exit 1
fi

TOTAL_TASKS=$(awk 'NR > 1 {count++} END {print count+0}' "${TASK_LIST}")

if (( TOTAL_TASKS == 0 )); then
    echo "ERROR: No FPS tasks found."
    exit 1
fi

if (( TOTAL_TASKS > TASKS_PER_NODE )); then
    echo "ERROR: ${TOTAL_TASKS} FPS calculations exceed available task slots."
    echo "TASKS_PER_NODE=${TASKS_PER_NODE}"
    exit 1
fi

echo
echo "FPS Similarity Island calculations"
echo
echo "SLURM job ID:     ${SLURM_JOB_ID:-direct}"
echo "Node:             $(hostname)"
echo "Partition:        ${SLURM_JOB_PARTITION:-${SLURM_PARTITION}}"
echo "FPS calculations: ${TOTAL_TASKS}"
echo "Started:          $(date)"
echo

PIDS=()
TASK_IDS=()

for (( TASK_ID=1; TASK_ID<=TOTAL_TASKS; TASK_ID++ )); do
    echo "Launching FPS task ${TASK_ID}"

    bash "${SCRIPT_DIR}/003.run_one_task.slurm" "${TASK_ID}" &

    PIDS+=("$!")
    TASK_IDS+=("${TASK_ID}")
done

FAILURES=0

echo
echo "All ${TOTAL_TASKS} FPS calculations launched."
echo "Waiting for completion..."
echo

for INDEX in "${!PIDS[@]}"; do
    PID="${PIDS[$INDEX]}"
    TASK_ID="${TASK_IDS[$INDEX]}"

    if wait "${PID}"; then
        echo "Task ${TASK_ID}: SUCCESS"
    else
        echo "Task ${TASK_ID}: FAILED"
        FAILURES=$((FAILURES + 1))
    fi
done

echo
echo "FPS calculations finished"
echo
echo "Finished:   $(date)"
echo "Tasks:      ${TOTAL_TASKS}"
echo "Successful: $((TOTAL_TASKS - FAILURES))"
echo "Failed:     ${FAILURES}"
echo

if (( FAILURES > 0 )); then
    exit 1
fi

exit 0
