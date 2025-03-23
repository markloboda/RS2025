#include <stdio.h>
#include <stdlib.h>

#define N 256 // Size of the matrix (N x N)
#define BLOCK_SIZE 64 // Size of the block

void mat_mult_tiled_iikkjj(int **A, int **B, int **C, int n, int block_size) {
    int i, j, k, ii, jj, kk;
    for (ii = 0; ii < n; ii += block_size) {
        for (kk = 0; kk < n; kk += block_size) {
            for (jj = 0; jj < n; jj += block_size) {
                for (i = ii; i < ii + block_size && i < n; i++) {
                    for (j = jj; j < jj + block_size && j < n; j++) {
                        for (k = kk; k < kk + block_size && k < n; k++) {
                            C[i][j] += A[i][k] * B[k][j];
                        }
                    }
                }
            }
        }
    }
}

int main() {
    int i, j;
    int **A = (int **)malloc(N * sizeof(int *));
    int **B = (int **)malloc(N * sizeof(int *));
    int **C = (int **)malloc(N * sizeof(int *));
    for (i = 0; i < N; i++) {
        A[i] = (int *)malloc(N * sizeof(int));
        B[i] = (int *)malloc(N * sizeof(int));
        C[i] = (int *)malloc(N * sizeof(int));
    }

    // Initialize matrices A and B with some values
    for (i = 0; i < N; i++) {
        for (j = 0; j < N; j++) {
            A[i][j] = i + j;
            B[i][j] = i - j;
            C[i][j] = 0;
        }
    }

    mat_mult_tiled_iikkjj(A, B, C, N, BLOCK_SIZE);

    for (i = 0; i < N; i++) {
        free(A[i]);
        free(B[i]);
        free(C[i]);
    }
    free(A);
    free(B);
    free(C);

    return 0;
}