import subprocess
import time

# Ordered configurations
CONFIGS = [
    # 8-bit unsigned
    # {"description": "4 clusters, 8-bit unsigned",  "args": ["--clusters", "4"]},
    # {"description": "8 clusters, 8-bit unsigned",  "args": ["--clusters", "8"]},
    # {"description": "16 clusters, 8-bit unsigned", "args": ["--clusters", "16"]},

    # Single precision
    {"description": "4 clusters, single precision",  "args": ["--single", "--clusters", "4"]},
    {"description": "8 clusters, single precision",  "args": ["--single", "--clusters", "8"]},
    {"description": "16 clusters, single precision", "args": ["--single", "--clusters", "16"]},

    # Double precision (no single flag means double precision)
    {"description": "4 clusters, double precision",  "args": ["--clusters", "4"]},
    {"description": "8 clusters, double precision",  "args": ["--clusters", "8"]},
    {"description": "16 clusters, double precision", "args": ["--clusters", "16"]},
]

FLAGS = ["--scalar", "--avx"]
SBATCH_SCRIPT = "sbatch_run.sh"
NUM_RUNS = 2

def run_configs():
    for i in range(NUM_RUNS):
        for flag in FLAGS:
            for config in CONFIGS:
                config_args = config["args"] + [flag]
                print(f"Running configuration: {config['description']} with {flag}")

                # Run the sbatch command
                cmd = ["sbatch", SBATCH_SCRIPT] + config_args
                print("Command:", " ".join(cmd))
                try:
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    print("Submitted:", result.stdout.strip())
                except subprocess.CalledProcessError as e:
                    print("Error running sbatch:", e.stderr.strip())

if __name__ == "__main__":
    run_configs()