#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/000.config.sh"

if [[ ! -s "${TASK_LIST}" ]]; then
    echo "ERROR: Missing task list: ${TASK_LIST}"
    echo "Run 002.make_task_list.sh first."
    exit 1
fi

N_TASKS=$(awk 'NR > 1 {count++} END {print count+0}' "${TASK_LIST}")

if (( N_TASKS == 0 )); then
    echo "ERROR: No FPS tasks found."
    exit 1
fi

if (( N_TASKS > TASKS_PER_NODE )); then
    echo "ERROR: ${N_TASKS} tasks exceed TASKS_PER_NODE=${TASKS_PER_NODE}."
    exit 1
fi

CPUS_REQUESTED=${N_TASKS}

echo
echo "Submitting FPS Similarity Island experiment"
echo
echo "FPS calculations: ${N_TASKS}"
echo "Partition:        ${SLURM_PARTITION}"
echo "CPUs requested:   ${CPUS_REQUESTED}"
echo "Walltime:         ${SLURM_TIME}"
echo

JOB_ID=$(sbatch \
    --parsable \
    --job-name=FPS_Islands \
    --partition="${SLURM_PARTITION}" \
    --nodes=1 \
    --ntasks=1 \
    --cpus-per-task="${CPUS_REQUESTED}" \
    --time="${SLURM_TIME}" \
    --export=ALL,FPS_WORK_ROOT="${WORK_ROOT}" \
    --chdir="${WORK_ROOT}" \
    --output="${WORK_ROOT}/FPS_slurm_%j.out" \
    "${SCRIPT_DIR}/004.run_FPS_chunks.slurm")

echo "Submitted job: ${JOB_ID}"
echo
