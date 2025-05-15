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

# Save the combined speedup plot
authority_fname = 'speedup_vs_clusters.png'
plt.savefig(authority_fname)
plt.close()
print(f"Saved combined speedup plot: {authority_fname}")
