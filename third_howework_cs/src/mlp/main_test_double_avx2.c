#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>

#include <immintrin.h>

#define INPUT_NODES 784  // 28*28 pixels
#define OUTPUT_NODES 10  // 10 digits (0-9)

#define NUM_TRAINING_IMAGES 60000
#define NUM_TEST_IMAGES 10000

double training_images[NUM_TRAINING_IMAGES][INPUT_NODES];
double training_labels[NUM_TRAINING_IMAGES][OUTPUT_NODES];
double test_images[NUM_TEST_IMAGES][INPUT_NODES];
double test_labels[NUM_TEST_IMAGES][OUTPUT_NODES];

// Dynamically allocated weights and biases
double **weight1 = NULL;
double **weight2 = NULL;
double *bias1 = NULL;
double *bias2 = NULL;

int HIDDEN_NODES;
int NUMBER_OF_EPOCHS;

double sigmoid(double x) {
    return 1.0 / (1.0 + exp(-x));
}

// Not really worth vectorizing in our case, because the size is
// only ever OUTPUT_NODES, which equals to 10.
int max_index(double arr[], int size) {
    int max_i = 0;
    for (int i = 1; i < size; i++) {
        if (arr[i] > arr[max_i]) {
            max_i = i;
        }
    }
    return max_i;
}

void load_mnist() {
    // Open the training images file
    FILE *training_images_file = fopen("./mnist_dataset/mnist_train_images.bin", "rb");
    if (training_images_file == NULL)
    {
        printf("Error opening training images file\n");
        exit(1);
    }

    // Open the training labels file
    FILE *training_labels_file = fopen("./mnist_dataset/mnist_train_labels.bin", "rb");
    if (training_labels_file == NULL)
    {
        printf("Error opening training labels file\n");
        exit(1);
    }

    // Open the test images file
    FILE *test_images_file = fopen("./mnist_dataset/mnist_test_images.bin", "rb");
    if (test_images_file == NULL)
    {
        printf("Error opening test images file\n");
        exit(1);
    }

    // Open the test labels file
    FILE *test_labels_file = fopen("./mnist_dataset/mnist_test_labels.bin", "rb");
    if (test_labels_file == NULL)
    {
        printf("Error opening test labels file\n");
        exit(1);
    }

    // Read the training images
    for (int i = 0; i < NUM_TRAINING_IMAGES; i++)
    {
        for (int j = 0; j < INPUT_NODES; j++)
        {
            unsigned char pixel;
            fread(&pixel, sizeof(unsigned char), 1, training_images_file);
            training_images[i][j] = (double)pixel / 255.0;
        }
    }

    // Read the training labels
    for (int i = 0; i < NUM_TRAINING_IMAGES; i++)
    {
        unsigned char label;
        fread(&label, sizeof(unsigned char), 1, training_labels_file);
        for (int j = 0; j < OUTPUT_NODES; j++)
        {
            if (j == label)
            {
                training_labels[i][j] = 1;
            }
            else
            {
                training_labels[i][j] = 0;
            }
        }
    }

    // Read the test images
    for (int i = 0; i < NUM_TEST_IMAGES; i++)
    {
        for (int j = 0; j < INPUT_NODES; j++)
        {
            unsigned char pixel;
            fread(&pixel, sizeof(unsigned char), 1, test_images_file);
            test_images[i][j] = (double)pixel / 255.0;
        }
    }

    // Read the test labels
    for (int i = 0; i < NUM_TEST_IMAGES; i++)
    {
        unsigned char label;
        fread(&label, sizeof(unsigned char), 1, test_labels_file);
        for (int j = 0; j < OUTPUT_NODES; j++)
        {
            if (j == label)
            {
                test_labels[i][j] = 1;
            }
            else
            {
                test_labels[i][j] = 0;
            }
        }
    }

    // Close the files
    fclose(training_images_file);
    fclose(training_labels_file);
    fclose(test_images_file);
    fclose(test_labels_file);
}


int test(
    double input[INPUT_NODES],
    double** weight1,
    double** weight2,
    double* bias1,
    double* bias2,
    int correct_label
) {
    int correct_predictions = 0;

    assert(HIDDEN_NODES % 8 == 0);
    assert(INPUT_NODES % 8 == 0);

    // Hack: we'll invert the loops to be i-j instead of j-i.

    // This will mean that we'll need several 256-bit AVX2 registers to store partial sums.
    // To avoid having to add biases for each hidden node at the end, we'll just simply initialize
    // the partial sums with them at the start.

    const int num_of_input_sum_segments = HIDDEN_NODES / 4;
    __m256d sum_input_segments[num_of_input_sum_segments];

    for (int segment_index = 0; segment_index < num_of_input_sum_segments; segment_index++) {
        sum_input_segments[segment_index] = _mm256_loadu_pd(&bias1[segment_index * 4]);
    }

    for (int j = 0; j < INPUT_NODES; j++) {
        // For the given input node `j`, we'll add the `input[j] * weight1[j][i]`,
        // where we go over all hidden nodes (`i`s). However, we'll do them in 4-chunk segments,
        // for which we prepared `sum_segments` above.

        __m256d input_value = _mm256_set1_pd(input[j]);

        const double* weight1_at_j = weight1[j];
        for (int segment_index = 0; segment_index < num_of_input_sum_segments; segment_index++) {
            __m256d weights = _mm256_loadu_pd(&weight1_at_j[segment_index * 4]);

            // What we're doing is essentially multiplication and addition,
            // or in other words FMA (fused multiply and add), which has a specific intrinsic.
            sum_input_segments[segment_index] = _mm256_fmadd_pd(
                input_value,
                weights,
                sum_input_segments[segment_index]
            );
        }
    }

    double hidden[HIDDEN_NODES];
    for (int segment_index = 0; segment_index < num_of_input_sum_segments; segment_index++) {
        double final_sums[4];
        _mm256_storeu_pd(final_sums, sum_input_segments[segment_index]);

        hidden[segment_index * 4] = sigmoid(final_sums[0]);
        hidden[segment_index * 4 + 1] = sigmoid(final_sums[1]);
        hidden[segment_index * 4 + 2] = sigmoid(final_sums[2]);
        hidden[segment_index * 4 + 3] = sigmoid(final_sums[3]);
    }


    // Again, instead of adding the second bias at the end, we can just initialize the sums with them.
    const int num_of_output_sum_segments = OUTPUT_NODES / 8;
    __m256d sum_output_segments[num_of_output_sum_segments];

    for (int segment_index = 0; segment_index < num_of_output_sum_segments; segment_index++) {
        sum_output_segments[segment_index] = _mm256_loadu_pd(&bias2[segment_index * 4]);
    }


    for (int j = 0; j < HIDDEN_NODES; j++) {
        // For the given hidden node `j`, we'll add the `hidden[j] * weight2[j][i]`,
        // where we go over all hidden nodes (`i`s). However, we'll do them in 4-chunk segments,
        // for which we prepared `sum_segments` above.

        __m256d hidden_value = _mm256_set1_pd(hidden[j]);

        const double* weight2_at_j = weight2[j];
        for (int segment_index = 0; segment_index < num_of_output_sum_segments; segment_index++) {
            __m256d weights = _mm256_loadu_pd(&weight2_at_j[segment_index * 4]);

            // What we're doing is essentially multiplication and addition,
            // or in other words FMA (fused multiply and add), which has a specific intrinsic.
            sum_output_segments[segment_index] = _mm256_fmadd_pd(
                hidden_value,
                weights,
                sum_output_segments[segment_index]
            );
        }
    }

    double output_layer[OUTPUT_NODES];
    for (int segment_index = 0; segment_index < num_of_output_sum_segments; segment_index++) {
        double final_sums[4];
        _mm256_storeu_pd(final_sums, sum_output_segments[segment_index]);

        output_layer[segment_index * 4] = sigmoid(final_sums[0]);
        output_layer[segment_index * 4 + 1] = sigmoid(final_sums[1]);
        output_layer[segment_index * 4 + 2] = sigmoid(final_sums[2]);
        output_layer[segment_index * 4 + 3] = sigmoid(final_sums[3]);
    }


    const int index = max_index(output_layer, OUTPUT_NODES);

    correct_predictions = index == correct_label ? 1 : 0;
    return correct_predictions;
}

// utils




void allocate_memory() {
    weight1 = malloc(INPUT_NODES * sizeof(double *));
    for (int i = 0; i < INPUT_NODES; i++) {
        weight1[i] = malloc(HIDDEN_NODES * sizeof(double));
    }

    weight2 = malloc(HIDDEN_NODES * sizeof(double *));
    for (int i = 0; i < HIDDEN_NODES; i++) {
        weight2[i] = malloc(OUTPUT_NODES * sizeof(double));
    }

    bias1 = malloc(HIDDEN_NODES * sizeof(double));
    bias2 = malloc(OUTPUT_NODES * sizeof(double));
}

void free_memory() {
    for (int i = 0; i < INPUT_NODES; i++) {
        free(weight1[i]);
    }
    free(weight1);

    for (int i = 0; i < HIDDEN_NODES; i++) {
        free(weight2[i]);
    }
    free(weight2);
    free(bias1);
    free(bias2);
}


void init_weigths_and_biases() {
    // Initialize weights and biases with random values
    for (int i = 0; i < INPUT_NODES; i++) {
        for (int j = 0; j < HIDDEN_NODES; j++) {
            weight1[i][j] = 0.1; // Random value between -1 and 1
        }
    }

    for (int i = 0; i < HIDDEN_NODES; i++) {
        for (int j = 0; j < OUTPUT_NODES; j++) {
            weight2[i][j] = 0.1; // Random value between -1 and 1
        }
    }

    for (int i = 0; i < HIDDEN_NODES; i++) {
        bias1[i] = 0.1; // Random value between -1 and 1
    }

    for (int i = 0; i < OUTPUT_NODES; i++) {
        bias2[i] = 0.1; // Random value between -1 and 1
    }
}



int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <hidden_nodes> <number_of_epochs> \n", argv[0]);
        return 1;
    }

    HIDDEN_NODES = atoi(argv[1]);

    // load weights and biases
    allocate_memory();
    init_weigths_and_biases();
    

    // load mnist dataset
    load_mnist();
    int correct_outcomes; 
    
    // measuring time
    clock_t start, end;
    double cpu_time_used = 0.0;


    
    cpu_time_used = 0.0;
    // Train the network
    correct_outcomes = 0;
    for (int i = 0; i < NUM_TRAINING_IMAGES; i++)
    {
        start = clock();
        correct_outcomes += test(training_images[i], weight1, weight2, bias1, bias2, max_index(training_labels[i], OUTPUT_NODES));
        end = clock();
        cpu_time_used += ((double) (end - start)) / CLOCKS_PER_SEC;
    }
    printf("Average time: %f seconds\n", cpu_time_used / NUM_TRAINING_IMAGES);

    
    free_memory();
    return 0;
}
