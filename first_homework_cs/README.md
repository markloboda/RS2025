# First Homework assignment


## First task 

In the first task, you will evaluate the performance of the O3 processor model that we developed during the lab exercises. To carry out this assessment, you will use the Whetstone benchmark, which can be found in the `workload/Whetstone/` folder.

### Whetstone benchmark

The Whetstone benchmark is an one of the method used to evaluate CPU performance, particularly for scientific applications. It consists of several modules that represent a range of operations commonly performed in scientific programs. The benchmark utilizes a variety of C functions, including sin, cos, sqrt, exp, and log, along with integer and floating-point mathematical operations, array accesses, conditional branches, and procedure calls. 

### Objectives 

1. Evaluate the performance of the out-of-order (OoO) processor by running the Whetstone benchmark in GEM5. Modify the following parameters of the out-of-order (O3) processor:

- **Issue Width:** 1, 2, 4, 8  
- **Reorder Buffer (ROB) Size:** 2, 4, 8, 16, 32 

Run the Whetstone benchmark for each combination of these parameters and record the results. When analyzing performance, consider the following metrics:
- **IPC** (Instructions Per Cycle)
- **CPI** (Cycles Per Instruction)

Number of points: 3

2. Examine the effect of branch prediction on the O3 processor's performance. For this task, you will need to modify the branch prediction technique in the O3 processor. Regarding the branch prediction, you should consider the following predictors:

- **Local Branch Predictor (LocalBP)**  
- **Multiperspective Perceptron TAGE Predictor (64KB)** ([Reference](https://www.jilp.org/vol8/v8paper1.pdf))  

For every predictor, assess the performance of O3 processor with the following parameters:
- **Issue Width:** 4, **ROB Size:** 32
- **Issue Width:** 4, **ROB Size:** 64

When comparing performance beside CPI, account also the number of mispredicted branches (**branchMispredicts**) as a key metric.

Number of points: 2

3. Analyzing the Impact of Functional Units

Your task is to alter the number of functional units in the O3 processor and evaluate the performance of the Whetstone benchmark. The following configurations should be considered:

- **Integer ALU:** 2 
- **Integer MUL/DIV:** 1
- **FP ALU:** 1
- **FP MUL/DIV:** 1

Note: The default configuration of Functional Units are found on the [following link](https://github.com/gem5/gem5/blob/186a913a48f13bdd484fcdef17ac3e28d2b8b4c9/src/cpu/o3/FuncUnitConfig.py#L45).

Number of bonus points: 2 

Note: The bonus points will be added to the final grade of the homework. Just the students who have completed the first two tasks will be eligible to receive the bonus points.

## Second task 

In the second task, you will need to assess the influence of cache size on the performance of the tilled matrix multiplication program. In the folder `workload/MatMult/`, you will find three versions of the matrix multiplication program, which differ in the way how they access memory. 
- **mat_mult1.c** 
- **mat_mult2.c**
- **mat_mult3.c**

### Objectives

1. First, assess the performance of matrix multiplication programs with the following cache sizes:

- **L1 Data Cache:** 1 KiB, 2 KiB, 4 KiB, 8 KiB
- **L2 Cache:** 32 KiB, 64 KiB
- The associativity of the caches should be 16-way set associative.

You should analyze the performance for every combination of the cache sizes. When evaluating the performance, consider the following metrics:
- **Instructions per Cycle (IPC)**
- **Cycles**
- **L1 Data Cache Miss Rate** 
- **L2 Cache Miss Rate** 

Metrics that should be considered in GEM5 statistics::
- `l1_dcache.WriteReq.misses::total`
- `l1_dcache.ReadReq.misses::total`
- `l1_dcache.WriteReq.hits::total`
- `l1_dcache.ReadReq.hits::total`
- `l2_cache.overallHits::total`
- `l2_cache.overallMisses::total`

Note: This step should be performed with the every version of the matrix multiplication.

Number of points: 4

2. Assess the performance of matrix multiplication under different cache associativity. You should consider the 1, 2, 4, 8, and 16-way set associative cache configurations. The cache sizes should be as follows: L1 Data Cache: 4KB and L2 Cache: 256KB.

Number of points: 1

## Submission

You should submit a report (max. 3 page) discussing the results of the experiments. Additionally, you should provide the source code of the modified programs and batch scripts used in the experiments.

## Warning 

Compile the programs in gem5 apptainer, using the bash script `make_apptainer.sh`.