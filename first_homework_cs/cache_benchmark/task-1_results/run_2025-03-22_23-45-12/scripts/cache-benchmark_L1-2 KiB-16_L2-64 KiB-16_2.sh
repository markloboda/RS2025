#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-cache-perf_bKyzIu
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output="/d/hpc/home/sg7710/rs/rs-dn1/cache_benchmark/results/run_2025-03-22_23-45-12/scripts/cache-benchmark_L1-2 KiB-16_L2-64 KiB-16_2.log"
#SBATCH --time=00:18:00

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86

srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt \
    --outdir="/d/hpc/home/sg7710/rs/rs-dn1/cache_benchmark/results/run_2025-03-22_23-45-12/benchmarks/L1-2 KiB-16_L2-64 KiB-16_2" cache_benchmark.py \
        --l1_size="2 KiB" --l2_size="64 KiB" \
        --l1_assoc="16" --l2_assoc="16" \
        --mult_version="2"

