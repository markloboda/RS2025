#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=runner
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=runner.log
#SBATCH --time=00:20:00

declare -a configurations=("2" "4" "8" "16")

for idx in "${!configurations[@]}"; do
    NUM_CORES=${configurations[$idx]}
    PROGRAM="../workload/pi/pi_optimized.bin"
    sbatch job.sh $PROGRAM $NUM_CORES
    PROGRAM="../workload/pi/pi_falsesharing.bin"
    sbatch job.sh $PROGRAM $NUM_CORES
done