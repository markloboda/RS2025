#!/bin/bash

AVX_FLAGS=""
PROGRAM="k-means_sca_double.c"

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
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Compile
gcc -O3 -lm $AVX_FLAGS -o main.out "$PROGRAM"

# Run
srun --reservation=fri --constraint=amd ./main.out

# Clean up
rm main.out
