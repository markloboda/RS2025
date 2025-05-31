#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --output=log_naive_CU4.txt
#SBATCH --job-name=naive_CU4

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM5_PATH=$GEM5_ROOT/build/VEGA_X86/
APPTAINER_IMG=$GEM5_WORKSPACE/gcn-gpu_v24-0.sif

apptainer exec $APPTAINER_IMG $GEM5_PATH/gem5.opt   --outdir=naive_CU4_stats   $GEM5_ROOT/configs/example/apu_se.py -n 3   --num-compute-units 4 --gfx-version="gfx902"   -c ./histogram/bin/histogram_naive
