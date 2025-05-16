#!/usr/bin/env bash
set -ex

gcc ./src/mlp/main_test_float_sca.c -o ./src/mlp/main_test_float_sca -O3 -lm -Wno-unused-result
