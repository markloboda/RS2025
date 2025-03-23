#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=cpu_benchmark
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=cpu_benchmark.log
#SBATCH --time=00:20:00

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86

WIDTH=$1
ROB_SIZE=$2
NUM_INT_REGS=$3
NUM_FP_REGS=$4

echo "Running with width: $WIDTH, rob_size: $ROB_SIZE, num_int_regs: $NUM_INT_REGS, num_fp_regs: $NUM_FP_REGS"
srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt --outdir=out/task2/mptp/out_${WIDTH}_${ROB_SIZE}_${NUM_INT_REGS}_${NUM_FP_REGS} cpu_benchmark.py --width $WIDTH --rob_size $ROB_SIZE --num_int_regs $NUM_INT_REGS --num_fp_regs $NUM_FP_REGS