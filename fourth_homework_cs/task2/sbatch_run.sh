#!/bin/bash

# Job name:
#SBATCH --job-name=test
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1  
#SBATCH --cpus-per-task=1 
#SBATCH --time=00:10:00
#SBATCH --output=test_tc.out
#SBATCH --constraint=amd
#SBATCH --reservation=fri
#SBATCH --propagate=STACK
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1

module load CUDA

FILE=mat_mult_solution
SM_ARCH=70


nvcc -o ${FILE}.out  -arch=sm_${SM_ARCH} ${FILE}.cu
./${FILE}.out

cuobjdump -ptx ${FILE}.out > ${FILE}.ptx

rm ${FILE}.out
