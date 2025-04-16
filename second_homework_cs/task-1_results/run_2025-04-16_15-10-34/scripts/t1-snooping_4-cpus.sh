#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-hw2_t1-qH/2ea
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output="task-1_results/run_2025-04-16_15-10-34/logs/t1-snooping_4-cpus.log"
#SBATCH --time=01:00:00

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86

echo "Running smp_benchmark.py"
srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt \
    --outdir="task-1_results/run_2025-04-16_15-10-34/results/4-cpus" ./smp_classic/smp_benchmark.py \
        --num_cores="4"

