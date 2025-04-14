import os
import matplotlib.pyplot as plt

# Create the plots directory if it does not exist
os.makedirs("plots", exist_ok=True)

# Processor configurations
cores = [2, 4, 8, 16]

# ----- Data based on your measurements -----
# Average CPI across cores:
# For false sharing, using the available average values from each file:
cpi_false = [
    (2.277441 + 2.235428) / 2,       # 2 cores (out_pi_falsesharing.bin_2)
    (3.119813 + 3.050346 + 3.049331 + 3.048485) / 4,  # 4 cores (out_pi_falsesharing.bin_4)
    (3.18898 + 3.050165 + 3.048094 + 3.04655 + 3.046007 + 3.046187 + 3.046561 + 3.047202) / 8,  # 8 cores (out_pi_falsesharing.bin_8)
    (3.276677 + 3.026479 + 3.410525 + 3.426494 + 3.023226 + 3.023986 + 3.024463 + 3.025427 + 
     3.022938 + 3.020134 + 3.463524 + 3.288121 + 3.334909 + 3.428166 + 3.296898 + 3.408122) / 16  # 16 cores (out_pi_falsesharing.bin_16)
]

# For optimized runs:
cpi_opt = [
    (2.211549 + 2.168958) / 2,  # 2 cores (out_pi_optimized.bin_2)
    (2.256581 + 2.171261 + 2.170275 + 2.169415) / 4,  # 4 cores (out_pi_optimized.bin_4)
    (2.347629 + 2.176976 + 2.174798 + 2.173346 + 2.172534 + 2.172549 + 2.172178 + 2.172108) / 8,  # 8 cores (out_pi_optimized.bin_8)
    (2.532231 + 2.190661 + 2.186594 + 2.183734 + 2.181987 + 2.181635 + 2.181461 + 2.181347 +
     2.180795 + 2.180394 + 2.180131 + 2.180044 + 2.179496 + 2.179354 + 2.178929 + 2.178982) / 16  # 16 cores (out_pi_optimized.bin_16)
]

# Cache invalidations:
# For false sharing:
inv_false = [300.0, 750394.0, 750534.0, 678629.0]
# For optimized:
inv_opt = [320.0, 403.0, 566.0, 1026.0]

# Network traffic (Request_Control message counts):
# For false sharing:
req_false = [2000810.0, 3501110.0, 3501582.0, 2939586.0]
# For optimized:
req_opt = [844.0, 1130.0, 1664.0, 2986.0]

# ----- Plotting Figure 1: Average CPI vs. Number of Processors -----
plt.figure(figsize=(8, 6))
plt.plot(cores, cpi_false, marker='o', linestyle='-', color='red', label='False Sharing')
plt.plot(cores, cpi_opt, marker='s', linestyle='--', color='green', label='Optimized')
plt.xlabel('Number of Processors')
plt.ylabel('Average CPI')
plt.title('Average CPI vs. Number of Processors')
plt.xticks(cores)
plt.legend()
plt.grid(True)
plt.tight_layout()
# Save the figure
plt.savefig("plots/average_cpi.png")
plt.close()

# ----- Plotting Figure 2: Cache Invalidation Counts vs. Number of Processors -----
plt.figure(figsize=(8, 6))
plt.plot(cores, inv_false, marker='o', linestyle='-', color='red', label='False Sharing')
plt.plot(cores, inv_opt, marker='s', linestyle='--', color='green', label='Optimized')
plt.xlabel('Number of Processors')
plt.ylabel('Cache Invalidations')
plt.title('Cache Invalidation Counts vs. Number of Processors')
plt.xticks(cores)
plt.yscale('log')  # Use a logarithmic scale for clarity
plt.legend()
plt.grid(True, which='both', linestyle=':', linewidth=0.5)
plt.tight_layout()
# Save the figure
plt.savefig("plots/cache_invalidations.png")
plt.close()

# ----- Plotting Figure 3: Network Traffic (Request_Control) vs. Number of Processors -----
plt.figure(figsize=(8, 6))
plt.plot(cores, req_false, marker='o', linestyle='-', color='red', label='False Sharing')
plt.plot(cores, req_opt, marker='s', linestyle='--', color='green', label='Optimized')
plt.xlabel('Number of Processors')
plt.ylabel('L1 Request_Control Messages')
plt.title('Network Traffic: Request_Control Messages vs. Number of Processors')
plt.xticks(cores)
plt.yscale('log')  # Use a logarithmic scale
plt.legend()
plt.grid(True, which='both', linestyle=':', linewidth=0.5)
plt.tight_layout()
# Save the figure
plt.savefig("plots/network_traffic.png")
plt.close()

print("Plots saved in the 'plots/' folder.")
