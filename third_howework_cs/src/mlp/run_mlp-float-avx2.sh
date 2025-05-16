#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --reservation=fri
#SBATCH --job-name=rs:dn3:mlp-avx2
#SBATCH --output=mlp_avx2.log
#SBATCH --chdir=/d/hpc/home/sg7710/rs/rs-dn3/src/mlp

set -e

echo "Compiling main_test_float_avx2.c"
gcc -O3 -lm -mavx2 -march=native -Wno-unused-result main_test_float_avx2.c -o main_test_float_avx2

echo "Running main_test_float_avx2"
./main_test_float_avx2 1024

echo "Done!"
