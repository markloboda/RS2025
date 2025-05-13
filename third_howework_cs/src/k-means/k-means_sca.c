#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdint.h>

#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image.h"
#include "stb_image_write.h"

// #define USE_AVX
#ifdef USE_AVX
#include <immintrin.h>
#endif

#define NUM_CLUSTERS 16
#define MAX_ITERATIONS 10000
#define THRESHOLD 0.0001


unsigned long long rdtsc() {
    unsigned int hi, lo;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((unsigned long long)lo) | (((unsigned long long)hi) << 32);
}

// Define cluster structure
struct Cluster {
    double centroid;
    int num_points;
    int* points;
};

#ifdef USE_AVX
__m256d __mm256_abs_pd(__m256d x) {
    __m256d sign_mask = _mm256_set1_pd(-0.0);
    return _mm256_andnot_pd(sign_mask, x); // This clears the sign bit
}
#endif

#ifdef USE_AVX
// Function to assign points (pixels) to clusters
void assign_points_to_clusters(struct Cluster clusters[], double* image, int image_size)
{
    int cluster_index = 0;
    double min_distance = __DBL_MAX__;

    // Preload centroids in chunks of 4 into __m256d registers
    __m256d centroid_vectors[NUM_CLUSTERS / 4]; // Array to hold 4 centroids per __m256d

    for (int k = 0; k < NUM_CLUSTERS; k += 4)
    {
        // Load 4 centroids into a __m256d register
        centroid_vectors[k / 4] = _mm256_set_pd(
            clusters[k + 3].centroid,
            clusters[k + 2].centroid,
            clusters[k + 1].centroid,
            clusters[k + 0].centroid
        );
    }

    for (int i = 0; i < image_size; i++)
    {
        double image_val = image[i];
        min_distance = __DBL_MAX__;
        cluster_index = 0;

        // Process centroids in chunks of 4 (loaded into __m256d registers)
        for (int k = 0; k < NUM_CLUSTERS; k += 4)
        {
            // Load 4 centroids for this chunk
            __m256d centroid_vector = centroid_vectors[k / 4];

            // Process using AVX
            __m256d image_value = _mm256_set1_pd(image_val);
            __m256d dist = _mm256_sub_pd(image_value, centroid_vector);
            __m256d abs_dist = _mm256_andnot_pd(_mm256_set1_pd(-0.0), dist); // abs

            double d[4];
            _mm256_storeu_pd(d, abs_dist);

            // Find the minimum distance in this chunk of 4 centroids
            for (int j = 0; j < 4; j++) {
                int cluster_id = k + j;
                if (cluster_id < NUM_CLUSTERS && d[j] < min_distance) {
                    min_distance = d[j];
                    cluster_index = cluster_id;
                }
            }
        }

        // Assign the point to the closest cluster
        clusters[cluster_index].points[clusters[cluster_index].num_points++] = i;
    }
}
#else
// Function to assign points (pixels) to clusters
void assign_points_to_clusters(struct Cluster clusters[], double* image, int image_size) {
    int cluster_index = 0;
    double min_distance = __FLT_MAX__;
    double* d = (double*)malloc(sizeof(double) * NUM_CLUSTERS);

    for (int i = 0; i < image_size; i++) {
        for (int k = 0; k < NUM_CLUSTERS; k++) {
            d[k] = fabs(image[i] - clusters[k].centroid);
        }
        // argmin of array d
        min_distance = d[0];
        cluster_index = 0;
        for (int k = 1; k < NUM_CLUSTERS; k++) {
            if (d[k] < min_distance) {
                min_distance = d[k];
                cluster_index = k;
            }
        }
        clusters[cluster_index].points[clusters[cluster_index].num_points++] = i;
    }

    free(d);
}
#endif

#ifdef USE_AVX
// Function to update centroids of clusters
void update_centroids(struct Cluster clusters[], double* image, int image_size)
{
    for (int i = 0; i < NUM_CLUSTERS; i+=4)
    {
        __m256d sums = _mm256_setzero_pd();

        int k = 0;
        for (; k < clusters[i].num_points; k+=4)
        {
            __m256d image_values = _mm256_set_pd(
                image[clusters[i].points[k]],
                image[clusters[i].points[k + 1]],
                image[clusters[i].points[k + 2]],
                image[clusters[i].points[k + 3]]
            );

            sums = _mm256_add_pd(sums, image_values);
        }

        double sums_arr[4];
        _mm256_storeu_pd(sums_arr, sums);
        double sum = sums_arr[0] + sums_arr[1] + sums_arr[2] + sums_arr[3];

        // Remainder if num_points is not a multiple of 4
        for (; k < clusters[i].num_points; k++)
        {
            sum += image[clusters[i].points[k]];
        }
    }
}
#else
// Function to update centroids of clusters
void update_centroids(struct Cluster clusters[], double* image, int image_size) {
    for (int i = 0; i < NUM_CLUSTERS; i++) {
        double sum = 0;
        for (int k = 0; k < clusters[i].num_points; k++) {
            int pixel_index = clusters[i].points[k];
            sum += image[pixel_index];
        }
        clusters[i].centroid = sum / clusters[i].num_points;
    }
}
#endif

// Function to calculate distance between two points

// K-means clustering function
void k_means(double* image, int image_size, struct Cluster* clusters) {

    // Initialize clusters
    struct Cluster clusters_temp[NUM_CLUSTERS];
    double error = 0;
    int iterations = 0;

    do {
        // Assign points (pixels) to clusters

        // Save old clusters
        for (int i = 0; i < NUM_CLUSTERS; i++) {
            clusters_temp[i] = clusters[i];
        }
        // Reinitialize cluster points
        for (int i = 0; i < NUM_CLUSTERS; i++) {
            clusters[i].num_points = 0;
        }


        // print centroids
        assign_points_to_clusters(clusters, image, image_size);
        // Update centroids
        update_centroids(clusters, image, image_size);

        // Calculate difference between old and new centroids
        error = 0;
        for (int i = 0; i < NUM_CLUSTERS; i++) {
            error += fabs(clusters[i].centroid - clusters_temp[i].centroid);
        }
        iterations++;

    } while (error > THRESHOLD && iterations < MAX_ITERATIONS);

    // Free memory
    // for (int i = 0; i < NUM_CLUSTERS; i++) {
    //     free(clusters[i].points);
    // }

}

// Function to segment image based on cluster values
void segment_image(double *image, struct Cluster* clusters, int image_size) {
    for (int i = 0; i < image_size; i++) {
        double min_distance = fabs(image[i] - clusters[0].centroid);
        int cluster_index = 0;
        for (int k = 1; k < NUM_CLUSTERS; k++) {
            double d = fabs(image[i] - clusters[k].centroid);
            if (d < min_distance) {
                min_distance = d;
                cluster_index = k;
            }
        }
        image[i] = (double)clusters[cluster_index].centroid*255.0;
    }
}

void print_with_spaces(long long n) {
    char buf[32], formatted[64];
    sprintf(buf, "%lld", n);

    int len = strlen(buf);
    int out = 0;
    int first_group = len % 3;
    if (first_group == 0) first_group = 3;

    for (int i = 0; i < len; i++) {
        if (i != 0 && (i - first_group) % 3 == 0)
            formatted[out++] = ' ';
        formatted[out++] = buf[i];
    }
    formatted[out] = '\0';

    printf("Time for K-means: %s cycles\n", formatted);
}

int main() {
    // Define sample grayscale image
    long long unsigned int start, end, cycles;

    // Load image from file and allocate space for the output image
    char image_name[] = "./bosko_grayscale.jpg";
    int width, height, cpp;
    // load only gray scale image
    unsigned char *h_imageIn = stbi_load(image_name, &width, &height, &cpp, STBI_grey);
    if (h_imageIn == NULL)
    {
        printf("Error reading loading image %s!\n", image_name);
        exit(EXIT_FAILURE);
    }
    // printf("Loaded image %s of size %dx%d.\n", image_name, width, height);
    // printf("Image is %d bytes per pixel.\n", cpp);
    // // Save grayscale image to file
    // printf("Size of image is %ld, %ld\n", sizeof(unsigned char), sizeof(h_imageIn));
    // stbi_write_jpg("bosko_grayscale.jpg", width, height,STBI_grey, h_imageIn, 100);

    double *image_pixels = (double*)malloc(sizeof(double) * width * height);
    // convert to grayscale
    for (int i = 0; i < height; i++) {
        for (int j = 0; j < width; j++) {
            image_pixels[i*width + j] = h_imageIn[i * width + j]/255.0;
        }
    }

    int image_size = width * height;

    // cluster centroids
    struct Cluster clusters[NUM_CLUSTERS];

    for (int i = 0; i < NUM_CLUSTERS; i++) {
        clusters[i].points = (int*)malloc(sizeof(int) * image_size);
    }

    // Initialize centroids randomly
    for (int i = 0; i < NUM_CLUSTERS; i++) {
        clusters[i].centroid = i*1.0/(NUM_CLUSTERS-1);
        clusters[i].num_points = 0;
    }

    // Perform K-means clustering
#ifdef USE_AVX
    printf("\nUsing AVX instructions...\n");
#else
    printf("Using scalar instructions...\n");
#endif

    start = rdtsc();
    k_means(image_pixels, image_size, clusters);
    end = rdtsc();
    cycles = end - start;
    print_with_spaces(cycles);

    //print cluster centroids
    // printf("Cluster centroids:\n");
    // for (int i = 0; i < NUM_CLUSTERS; i++) {
    //     printf("Cluster %d: %.2f\n", i + 1, clusters[i].centroid);
    // }

    // // Segment image
    segment_image(image_pixels, clusters, image_size);

    // Save image to file
    for(int i = 0; i < height; i++) {
        for(int j = 0; j < width; j++) {
            h_imageIn[i*width + j] = (char)(image_pixels[i*width + j]);
        }
    }
    // Free memory

    stbi_write_jpg("bosko_k-means.jpg", width, height, STBI_grey, h_imageIn, 100);
    free(image_pixels);

    return 0;
}
