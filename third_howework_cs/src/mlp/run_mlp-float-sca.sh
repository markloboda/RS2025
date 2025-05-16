#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --reservation=fri
#SBATCH --job-name=rs:dn3:mlp-sca
#SBATCH --output=mlp_sca.log
#SBATCH --chdir=/d/hpc/home/sg7710/rs/rs-dn3/src/mlp

set -e

echo "Compiling main_test_float_sca.c"
gcc -O3 -lm -march=native -Wno-unused-result ./main_test_float_sca.c -o ./main_test_float_sca

echo "Running main_test_float_sca"
./main_test_float_sca 1024

echo "Done!"
