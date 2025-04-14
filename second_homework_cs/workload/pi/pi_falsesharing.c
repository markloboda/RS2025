#include <stdio.h>
#include <omp.h>
#include <stdlib.h>
#include <string.h>

#define NUM_STEPS 1000000

int main() {
    double step = 1.0 / NUM_STEPS;
    double pi = 0.0;

    // Initialize OpenMP
    // get number of threads
    int num_threads = omp_get_max_threads();
    omp_set_num_threads(num_threads);


    // Allocate memory for the sum array
    double* sum = (double*)malloc(num_threads * sizeof(double));
    memset(sum, 0, num_threads * sizeof(double));  // Initialize to zero

    #pragma omp parallel
    {
        int id = omp_get_thread_num();
        int num_threads = omp_get_num_threads();
        sum[id] = 0.0;  // Each thread initializes its sum
        
        for (int i = id; i < NUM_STEPS; i += num_threads) {
            double x = (i + 0.5) * step;
            sum[id] += 4.0 / (1.0 + x * x);
        }
    }

    // Summing up partial results
    for (int i = 0; i < num_threads; i++) {
        pi += sum[i];
    }

    pi *= step;
    printf("PI (with false sharing) = %.15f\n", pi);
    
    // Free allocated memory
    free(sum);
    return 0;
}