#!/usr/bin/env bash
set -ex

gcc -O2 ./src/mlp/main_test_double_sca.c -o main_test_double_sca -lm -Wno-unused-result
