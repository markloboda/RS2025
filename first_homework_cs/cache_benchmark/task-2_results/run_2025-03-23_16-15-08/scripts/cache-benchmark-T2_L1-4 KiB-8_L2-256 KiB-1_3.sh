#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-cache-perf-t2_UjvVj1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output="/d/hpc/home/sg7710/rs/rs-dn1/cache_benchmark/task-2_results/run_2025-03-23_16-15-08/scripts/cache-benchmark-T2_L1-4 KiB-8_L2-256 KiB-1_3.log"
#SBATCH --time=00:18:00

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86

srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt \
    --outdir="/d/hpc/home/sg7710/rs/rs-dn1/cache_benchmark/task-2_results/run_2025-03-23_16-15-08/benchmarks/L1-4 KiB-8_L2-256 KiB-1_3" cache_benchmark.py \
        --l1_size="4 KiB" --l2_size="256 KiB" \
        --l1_assoc="8" --l2_assoc="1" \
        --mult_version="3"

