#!/bin/bash

AVX_FLAGS=""
PROGRAM="k-means_sca_double.c"
OUTFILE="main.out"
CLUSTER_DEFINE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
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
gcc -O3 -lm $AVX_FLAGS $CLUSTER_DEFINE -o "$OUTFILE" "$PROGRAM"

# Run
srun --reservation=fri --constraint=amd ./"$OUTFILE"

# Clean up
rm -f "$OUTFILE"
