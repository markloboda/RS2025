#!/usr/bin/env bash
set -ex

gcc ./src/mlp/main_test_float_avx2.c -o ./src/mlp/main_test_float_avx2 -O3 -mavx2 -lm -Wno-unused-result
