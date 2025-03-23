#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=runner
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=runner.log
#SBATCH --time=00:20:00

declare -a widths=("4")
declare -a rob_sizes=("32" "64")
declare -a num_int_regs=("60")
declare -a num_fp_regs=("60")

for WIDTH_INDEX in "${!widths[@]}"; do
    for ROB_SIZE_INDEX in "${!rob_sizes[@]}"; do
        for NUM_INT_REGS_INDEX in "${!num_int_regs[@]}"; do
            for NUM_FP_REGS_INDEX in "${!num_fp_regs[@]}"; do
                WIDTH=${widths[$WIDTH_INDEX]}
                ROB_SIZE=${rob_sizes[$ROB_SIZE_INDEX]}
                NUM_INT_REGS=${num_int_regs[$NUM_INT_REGS_INDEX]}
                NUM_FP_REGS=${num_fp_regs[$NUM_FP_REGS_INDEX]}

                sbatch job.sh $WIDTH $ROB_SIZE $NUM_INT_REGS $NUM_FP_REGS
            done
        done
    done
done