import matplotlib.pyplot as plt
import pandas as pd

# Read raw data from external file 'results.txt'
with open('results.txt', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

# Parse lines into records
data = []
for line in lines:
    parts = line.split(';')
    precision = parts[0]
    isa = parts[1]
    clusters = int([p for p in parts if p.startswith('NUM_CLUSTERS')][0].split('=')[1])
    cycles = int([p for p in parts if p.startswith('CYCLES')][0].split('=')[1])
    data.append({'precision': precision, 'isa': isa, 'clusters': clusters, 'cycles': cycles})

# Build DataFrame
df = pd.DataFrame(data)

# Compute average cycles per configuration
grouped = df.groupby(['precision', 'isa', 'clusters'], as_index=False)['cycles'].mean()

# Pivot to get SCALAR & AVX side by side for speedup calculation
df_pivot = grouped.pivot_table(index=['precision', 'clusters'], columns='isa', values='cycles').reset_index()

# Calculate speedup = SCALAR / AVX
df_pivot['speedup'] = df_pivot['SCALAR'] / df_pivot['AVX']

# Combined speedup plot: one curve per precision
plt.figure()
for prec in df_pivot['precision'].unique():
    subset = df_pivot[df_pivot['precision'] == prec]
    plt.plot(subset['clusters'], subset['speedup'], marker='o', label=f"{prec} Precision")

plt.xlabel('Number of Clusters')
plt.ylabel('Speedup (SCALAR / AVX)')
plt.title('K-Means Speedup: Scalar vs AVX by Precision')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('speedup_vs_clusters.png')
plt.close()
print("Saved combined speedup plot: speedup_vs_clusters.png")

# Average cycle plot split by precision
for prec in grouped['precision'].unique():
    plt.figure()
    subset_prec = grouped[grouped['precision'] == prec]
    for isa in subset_prec['isa'].unique():
        subset = subset_prec[subset_prec['isa'] == isa]
        plt.plot(subset['clusters'], subset['cycles'], marker='o', label=f"{isa}")

    plt.xlabel('Number of Clusters')
    plt.ylabel('Average Cycles')
    plt.title(f'Average Cycles per Configuration - {prec} Precision')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    filename = f'avg_cycles_per_config_{prec.lower()}.png'
    plt.savefig(filename)
    plt.close()
    print(f"Saved average cycle plot: {filename}")
