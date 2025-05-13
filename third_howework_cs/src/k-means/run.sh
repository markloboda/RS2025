#!/bin/bash

AVX_FLAG=""

while [[ "$1" == "--avx" ]]; do
  AVX_FLAG="-DUSE_AVX"
  shift
done

while [[ "$1" == "--avx512" ]]; do
  AVX_FLAG="-DUSE_AVX512"
  shift
done

if [ -n "$AVX_FLAG" ]; then
  gcc -O3 -march=znver1 -lm $AVX_FLAG -o main.out k-means_sca.c
else
  gcc -O3 -lm -o main.out k-means_sca.c
fi

srun --reservation=fri --constraint=amd ./main.out
rm main.out