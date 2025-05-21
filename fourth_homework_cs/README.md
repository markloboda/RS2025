# Fourth homework assignment

## Task 1: Analyzing the performance of GPU kernels in GEM5 (5 points)


In this task, you will evaluate the performance characteristics of a histogram computation kernel using the GEM5 GPU simulator. The histogram kernel is a algorithm that processes an input image and computes the frequency distribution of pixel values. The input image `lena.jpg` is provided in the `histogram/` directory. The histogram is computed over 256 bins, corresponding to the pixel values ranging from 0 to 255. 

You are tasked with analyzing and comparing the performance of two kernel implementations:

- Naive implementation: This version updates a single histogram stored in global memory, resulting in frequent memory contention.

- Optimized implementation with privatization: In this version, each group of threads maintains a private copy of the histogram. After the parallel computation completes, these private histograms are merged into a single global histogram.

Both kernel versions are provided in the `histogram/` directory. The implementations are written in HIP and are configured to run within the GEM5 GPU simulation environment.

To build and simulate the kernels, use the provided Makefile in conjunction with the `make_apptainer.sh` script. This script automates the build process inside the pre-configured container environment for GEM5 GPU simulation.

### Experiment Setup:

1. Set the number of compute units to 2, 4, and 8.
2. Run the both of the histogram kernels for each configuration.
3. To observe the impact of false sharing, observe following metrics:
   - Mean load latency (`loadLatencyDist::mean`)
   - Avergage number of executed vector ALU instructions (`vALUInsts`)
   - Average number of read and writes to shared memory (`groupReads` `groupWrites`)
   - Average number of access to the shared memory (`ldsBankAccess`)
   - Average number of cycles (`totalCycles`)
   - Average number of vector per cycle (`vpc`)

> Note: When analyzing the results in the `stats.txt` file, you will notice that each performance metric appears **twice**. The **first occurrence** of each metric corresponds to the period **during GPU kernel execution**.
The **second occurrence** is collected **after the GPU kernel has completed**. For the task at hand, you should **focus on the first set of statistics**, as they reflect the actual behavior and performance characteristics of the GPU kernel while it is executing.



## Task 2: Implementing Matrix multiplication using TensorCores (5 points)

In this task, you will implement matrix multiplication using the WMMA PTX API and TensorCore, employing a block-based approach to improve performance. First, partition the input matrices into blocks and leverage TensorCore to accelerate block matrix multiplication. Implement the CUDA kernel (mm_block_tc) to handle block-wise matrix multiplication efficiently. Then, compare the execution time of your TensorCore-accelerated kernel against a naive matrix multiplication (mm_naive) implementation for varying sizes of square matrices (256, 512, 1024, 2048, and 4096). In the given program, the block size is equal to the number of threads in a warp; you can change it to suit your needs. To enable fair comparison, one should compare the performance of the naive kernel and the TensorCore accelerated kernel under the same grid and block size configuration. 

## Analysis and Reporting:
Describe your results in a report (two pages max). 
