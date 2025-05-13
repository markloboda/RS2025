#!/bin/bash
#
#SBATCH --job-name=kmeans
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=logs.log
#SBATCH --constraint=amd
#SBATCH --reservation=fri
#SBATCH --propagate=STACK

AVX_FLAGS=""
PROGRAM="k-means_sca_double.c"
CLUSTER_DEFINE=""

# Generate a random output file name
OUTFILE=$(mktemp main_XXXXXX.out)

# Parse custom options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scalar)
      shift
      ;;
    --avx)
      AVX_FLAGS="$AVX_FLAGS -march=znver1 -DUSE_AVX -mavx2"
      shift
      ;;
    --avx512)
      AVX_FLAGS="$AVX_FLAGS -march=znver1 -DUSE_AVX512 -mavx512f"
      shift
      ;;
    --single)
      PROGRAM="k-means_sca_single.c"
      shift
      ;;
    --clusters)
      shift
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        CLUSTER_DEFINE="-DNUM_CLUSTERS=$1"
        shift
      else
        echo "Error: --clusters requires a numeric argument"
        exit 1
      fi
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Compile
gcc -O3 -lm $AVX_FLAGS $CLUSTER_DEFINE -o $OUTFILE "$PROGRAM"

# Run
chmod +x $OUTFILE
./$OUTFILE

# Clean up
rm -f $OUTFILE
