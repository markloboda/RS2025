#!/bin/bash
#SBATCH --reservation=fri
#SBATCH --job-name=rs-hw2_t3-2zmCdw
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output="task-3_results/run_2025-04-16_15-10-38/logs/t3-interconnection_4-cpus_point-to-point-network.log"
#SBATCH --time=01:00:00

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM_PATH=$GEM5_ROOT/build/X86

echo "Running network_benchmark.py"
srun apptainer exec $GEM5_WORKSPACE/gem5.sif $GEM_PATH/gem5.opt \
    --outdir="task-3_results/run_2025-04-16_15-10-38/results/4-cpus_point-to-point-network" ./network/network_benchmark.py \
        --num_cores="4" \
        --interconnection-network="point-to-point"

