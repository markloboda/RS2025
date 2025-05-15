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

float training_images[NUM_TRAINING_IMAGES][INPUT_NODES];
float training_labels[NUM_TRAINING_IMAGES][OUTPUT_NODES];
float test_images[NUM_TEST_IMAGES][INPUT_NODES];
float test_labels[NUM_TEST_IMAGES][OUTPUT_NODES];

// Dynamically allocated weights and biases
float **weight1;
float **weight2;
float *bias1;
float *bias2;

int HIDDEN_NODES;
int NUMBER_OF_EPOCHS;

float sigmoid(float x)
{
    return 1.0f / (1.0f + expf(-x));
}

int max_index(float arr[], int size) {
    int max_i = 0;
    for (int i = 1; i < size; i++) {
        if (arr[i] > arr[max_i]) {
            max_i = i;
        }
    }
    return max_i;
}




void load_mnist()
{
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
            training_images[i][j] = (float)pixel / 255.0f;
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
                training_labels[i][j] = 1.0f;
            }
            else
            {
                training_labels[i][j] = 0.0f;
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
            test_images[i][j] = (float)pixel / 255.0f;
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
                test_labels[i][j] = 1.0f;
            }
            else
            {
                test_labels[i][j] = 0.0f;
            }
        }
    }

    // Close the files
    fclose(training_images_file);
    fclose(training_labels_file);
    fclose(test_images_file);
    fclose(test_labels_file);
}

static inline float get_array_value_or_zero(
    const float* array,
    const unsigned int array_length,
    const unsigned int index
) {
    if (index >= array_length) {
        return 0.0f;
    }

    return array[index];
}

static inline float get_2d_array_value_or_zero(
    float** array,
    const unsigned int array_length_first_dimension,
    const unsigned int array_length_second_dimension,
    const unsigned int index_first_dimension,
    const unsigned int index_second_dimension
) {
    if (index_first_dimension >= array_length_first_dimension || index_second_dimension >= array_length_second_dimension) {
        return 0.0f;
    }

    return array[index_first_dimension][index_second_dimension];
}


int test(float input[INPUT_NODES], float** weight1, float** weight2, float* bias1, float* bias2, int correct_label)
{   
    int correct_predictions = 0;
    float hidden[HIDDEN_NODES];
    float output_layer[OUTPUT_NODES];

    // TODO rewriting with AVX2 below

    for (int i = 0; i < HIDDEN_NODES; i++) {
        float sum = 0.0f;

        for (int j = 0; j < INPUT_NODES; j += 8) {
            // If highest bit is 1, the input is unmasked. If the highest bit is zero, the input is masked out.
            const int input_0_mask = -1;
            const int input_1_mask = (j + 1) < HIDDEN_NODES ? -1 : 0;
            const int input_2_mask = (j + 2) < HIDDEN_NODES ? -1 : 0;
            const int input_3_mask = (j + 3) < HIDDEN_NODES ? -1 : 0;
            const int input_4_mask = (j + 4) < HIDDEN_NODES ? -1 : 0;
            const int input_5_mask = (j + 5) < HIDDEN_NODES ? -1 : 0;
            const int input_6_mask = (j + 6) < HIDDEN_NODES ? -1 : 0;
            const int input_7_mask = (j + 7) < HIDDEN_NODES ? -1 : 0;

            const __m256i input_load_mask = _mm256_setr_epi32(
                input_0_mask, input_1_mask, input_2_mask, input_3_mask,
                input_4_mask, input_5_mask, input_6_mask, input_7_mask
            );


            const __m256 loaded_inputs = _mm256_maskload_ps(&input[j], input_load_mask);


            const float weight1_0 = weight1[j][i];
            const float weight1_1 = get_2d_array_value_or_zero(weight1, INPUT_NODES, HIDDEN_NODES, j + 1, i);
            const float weight1_2 = get_2d_array_value_or_zero(weight1, INPUT_NODES, HIDDEN_NODES, j + 2, i);
            const float weight1_3 = get_2d_array_value_or_zero(weight1, INPUT_NODES, HIDDEN_NODES, j + 3, i);
            const float weight1_4 = get_2d_array_value_or_zero(weight1, INPUT_NODES, HIDDEN_NODES, j + 4, i);
            const float weight1_5 = get_2d_array_value_or_zero(weight1, INPUT_NODES, HIDDEN_NODES, j + 5, i);
            const float weight1_6 = get_2d_array_value_or_zero(weight1, INPUT_NODES, HIDDEN_NODES, j + 6, i);
            const float weight1_7 = get_2d_array_value_or_zero(weight1, INPUT_NODES, HIDDEN_NODES, j + 7, i);

            const __m256 loaded_weights = _mm256_set_ps(
                weight1_0, weight1_1, weight1_2, weight1_3,
                weight1_4, weight1_5, weight1_6, weight1_7
            );

            const __m256 multiplication_results = _mm256_mul_ps(loaded_inputs, loaded_weights);

            // TODO this can be optimized by using horizontal sums (three times)
            sum += multiplication_results[0];
            sum += multiplication_results[1];
            sum += multiplication_results[2];
            sum += multiplication_results[3];
            sum += multiplication_results[4];
            sum += multiplication_results[5];
            sum += multiplication_results[6];
            sum += multiplication_results[7];
        }

        sum += bias1[i];
        hidden[i] = sigmoid(sum);

    }

    for (int i = 0; i < OUTPUT_NODES; i++) {
        float sum = 0.0f;

        for (int j = 0; j < HIDDEN_NODES; j += 8) {
            // If highest bit is 1, the input is unmasked. If the highest bit is zero, the input is masked out.
            const int input_0_mask = -1;
            const int input_1_mask = (j + 1) < HIDDEN_NODES ? -1 : 0;
            const int input_2_mask = (j + 2) < HIDDEN_NODES ? -1 : 0;
            const int input_3_mask = (j + 3) < HIDDEN_NODES ? -1 : 0;
            const int input_4_mask = (j + 4) < HIDDEN_NODES ? -1 : 0;
            const int input_5_mask = (j + 5) < HIDDEN_NODES ? -1 : 0;
            const int input_6_mask = (j + 6) < HIDDEN_NODES ? -1 : 0;
            const int input_7_mask = (j + 7) < HIDDEN_NODES ? -1 : 0;

            const __m256i input_load_mask = _mm256_setr_epi32(
                input_0_mask, input_1_mask, input_2_mask, input_3_mask,
                input_4_mask, input_5_mask, input_6_mask, input_7_mask
            );


            const __m256 loaded_inputs = _mm256_maskload_ps(&hidden[j], input_load_mask);


            const float weight1_0 = weight2[j][i];
            const float weight1_1 = get_2d_array_value_or_zero(weight2, INPUT_NODES, HIDDEN_NODES, j + 1, i);
            const float weight1_2 = get_2d_array_value_or_zero(weight2, INPUT_NODES, HIDDEN_NODES, j + 2, i);
            const float weight1_3 = get_2d_array_value_or_zero(weight2, INPUT_NODES, HIDDEN_NODES, j + 3, i);
            const float weight1_4 = get_2d_array_value_or_zero(weight2, INPUT_NODES, HIDDEN_NODES, j + 4, i);
            const float weight1_5 = get_2d_array_value_or_zero(weight2, INPUT_NODES, HIDDEN_NODES, j + 5, i);
            const float weight1_6 = get_2d_array_value_or_zero(weight2, INPUT_NODES, HIDDEN_NODES, j + 6, i);
            const float weight1_7 = get_2d_array_value_or_zero(weight2, INPUT_NODES, HIDDEN_NODES, j + 7, i);

            const __m256 loaded_weights = _mm256_set_ps(
                weight1_0, weight1_1, weight1_2, weight1_3,
                weight1_4, weight1_5, weight1_6, weight1_7
            );

            const __m256 multiplication_results = _mm256_mul_ps(loaded_inputs, loaded_weights);

            // TODO this can be optimized by using horizontal sums (three times)
            sum += multiplication_results[0];
            sum += multiplication_results[1];
            sum += multiplication_results[2];
            sum += multiplication_results[3];
            sum += multiplication_results[4];
            sum += multiplication_results[5];
            sum += multiplication_results[6];
            sum += multiplication_results[7];
        }

        sum += bias2[i];
        output_layer[i] = sigmoid(sum);
    }

    int index = max_index(output_layer, OUTPUT_NODES);

    correct_predictions = index == correct_label ? 1 : 0;
    return correct_predictions;

    // TODO DEPRECATED below, rewriting with AVX2 above

    /*
    // Feedforward
    for (int i = 0; i < HIDDEN_NODES; i++)
    {
        float sum = 0.0f;
        for (int j = 0; j < INPUT_NODES; j++)
        {
            sum += input[j] * weight1[j][i];
        }
        sum += bias1[i];
        hidden[i] = sigmoid(sum);
    }

    for (int i = 0; i < OUTPUT_NODES; i++)
    {
        float sum = 0.0f;
        for (int j = 0; j < HIDDEN_NODES; j++)
        {
            sum += hidden[j] * weight2[j][i];
        }
        sum += bias2[i];
        output_layer[i] = sigmoid(sum);
    }
    int index = max_index(output_layer, OUTPUT_NODES);

    correct_predictions = index == correct_label ? 1 : 0;
     
    return correct_predictions;*/
}

// utils

void allocate_memory() {
    weight1 = malloc(INPUT_NODES * sizeof(float *));
    for (int i = 0; i < INPUT_NODES; i++) {
        weight1[i] = malloc(HIDDEN_NODES * sizeof(float));
    }

    weight2 = malloc(HIDDEN_NODES * sizeof(float *));
    for (int i = 0; i < HIDDEN_NODES; i++) {
        weight2[i] = malloc(OUTPUT_NODES * sizeof(float));
    }

    bias1 = malloc(HIDDEN_NODES * sizeof(float));
    bias2 = malloc(OUTPUT_NODES * sizeof(float));
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
        printf("Usage: %s <hidden_nodes>\n", argv[0]);
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

    printf("Correct outcomes: %i\n", correct_outcomes);
    printf("Average time: %f seconds\n", cpu_time_used / NUM_TRAINING_IMAGES);


    free_memory();
    return 0;
}
