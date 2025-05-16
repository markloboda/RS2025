#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --reservation=fri
#SBATCH --job-name=rs-hw3_t1-QRyyNYGkspoO
#SBATCH --output="benchmarks/benchmark_2025-05-15_17-54-15/t1_implementation-avx2_precision-float_hidden-layers-128_repetition-7.log"
#SBATCH --time=00:20:00

set -e
cd "/d/hpc/home/sg7710/rs/rs-dn3/src/mlp"

echo "Running main_test_float_avx2.c"
./main_test_float_avx2 128

echo "Done!"
