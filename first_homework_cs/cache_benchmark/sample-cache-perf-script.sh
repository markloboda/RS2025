#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-cache-perf
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=rs-cache-perf3.log
#SBATCH --time=00:30:00


GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86


srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt \
    --outdir=sample_cache_stats1_1core cache_benchmark.py \
        --l1_size=1KiB --l2_size=32KiB \
        --l1_assoc=16 --l2_assoc=16 \
        --mult_version=1
