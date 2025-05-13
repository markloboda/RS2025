#!/bin/bash

AVX_FLAG=""

while [[ "$1" == "--avx" ]]; do
  AVX_FLAG="-DUSE_AVX"
  shift
done

if [ -n "$AVX_FLAG" ]; then
  gcc -O3 -mavx2 -lm $AVX_FLAG -o main k-means_sca.c
else
  gcc -O3 -lm -o main k-means_sca.c
fi

srun --reservation=fri ./main
