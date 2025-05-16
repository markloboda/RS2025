#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --reservation=fri
#SBATCH --job-name=rs-hw3_t1-nBjImBPWUmm4
#SBATCH --output="benchmarks/benchmark_2025-05-15_17-54-15/t1_implementation-sca_precision-double_hidden-layers-1024_repetition-9.log"
#SBATCH --time=00:20:00

set -e
cd "/d/hpc/home/sg7710/rs/rs-dn3/src/mlp"

echo "Running main_test_double_sca.c"
./main_test_double_sca 1024

echo "Done!"
