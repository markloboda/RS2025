#!/bin/bash

for kernel in naive opt; do
  for cu in 2 4 8; do
    cat <<EOF > slurm_${kernel}_CU${cu}.sh
#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --output=log_${kernel}_CU${cu}.txt
#SBATCH --job-name=${kernel}_CU${cu}

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=\$GEM5_WORKSPACE/gem5
GEM5_PATH=\$GEM5_ROOT/build/VEGA_X86/
APPTAINER_IMG=\$GEM5_WORKSPACE/gcn-gpu_v24-0.sif

apptainer exec \$APPTAINER_IMG \$GEM5_PATH/gem5.opt \
  --outdir=${kernel}_CU${cu}_stats \
  \$GEM5_ROOT/configs/example/apu_se.py -n 3 \
  --num-compute-units $cu --gfx-version="gfx902" \
  -c ./histogram/bin/histogram_${kernel}
EOF
    sbatch slurm_${kernel}_CU${cu}.sh
  done
done
