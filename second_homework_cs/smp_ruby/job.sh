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

PROGRAM=$1
NUM_CORES=$2
PROGRAM_NAME=$(basename "$PROGRAM")

echo "Running with processor count: $NUM_CORES and program $PROGRAM_NAME"
srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt --outdir=out/out_${PROGRAM_NAME}_${NUM_CORES} ruby_benchmark.py --program $PROGRAM --num_cores $NUM_CORES
