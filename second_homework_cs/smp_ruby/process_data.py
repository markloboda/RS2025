import os
import re
import argparse
from collections import defaultdict

BASE_KEYS = [
    "simSeconds",
    "board.cache_hierarchy.ruby_system.L1Cache_Controller.Inv::total",
    "board.cache_hierarchy.ruby_system.L1Cache_Controller.I.Load::total",
    "board.cache_hierarchy.ruby_system.L1Cache_Controller.S.Load::total",
    "board.cache_hierarchy.ruby_system.L1Cache_Controller.E.Load::total",
    "board.cache_hierarchy.ruby_system.L1Cache_Controller.M.Load::total",
    "board.cache_hierarchy.ruby_system.L2Cache_Controller.L1_GETS",
    "board.cache_hierarchy.ruby_system.L2Cache_Controller.L1_GETX",
    "board.cache_hierarchy.ruby_system.network.msg_count.Request_Control",
    "board.cache_hierarchy.ruby_system.network.msg_count.Response_Data",
    "board.cache_hierarchy.ruby_system.network.msg_count.Writeback_Data"
]

def find_stats_files(root_folder):
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename == "stats.txt":
                yield os.path.join(dirpath, filename)

def extract_all_core_cpis(file_path):
    cpi_pattern = re.compile(r'board\.processor\.cores(\d+)\.core\.cpi')
    core_cpis = {}
    with open(file_path, 'r') as file:
        for line in file:
            match = cpi_pattern.match(line.strip())
            if match:
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 2:
                    try:
                        core_cpis[line.strip().split()[0]] = float(parts[1])
                    except ValueError:
                        core_cpis[line.strip().split()[0]] = parts[1]
    return core_cpis

def extract_stats(file_path, base_keys):
    stats = {}
    with open(file_path, 'r') as file:
        for line in file:
            for key in base_keys:
                if line.strip().startswith(key):
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) >= 2:
                        try:
                            stats[key] = float(parts[1])
                        except ValueError:
                            stats[key] = parts[1]
    stats.update(extract_all_core_cpis(file_path))
    return stats

def aggregate_stats(folder_path, base_keys):
    aggregated = defaultdict(dict)
    for file_path in find_stats_files(folder_path):
        run_name = os.path.basename(os.path.dirname(file_path))
        stats = extract_stats(file_path, base_keys)
        aggregated[run_name].update(stats)
    return aggregated

def save_data(aggregated_data, output_path, all_keys):
    with open(output_path, 'w') as f:
        for run, data in aggregated_data.items():
            f.write(f"[{run}]\n")
            for key in all_keys:
                value = data.get(key, 'N/A')
                f.write(f"{key}: {value}\n")
            f.write("\n")

def main():
    parser = argparse.ArgumentParser(
        description="Aggregate simulation stats from multiple stats.txt files in subfolders"
    )
    parser.add_argument("folder", help="Path to the root folder containing stats.txt files")
    args = parser.parse_args()

    all_keys = set(BASE_KEYS)
    for file_path in find_stats_files(args.folder):
        cpi_keys = extract_all_core_cpis(file_path).keys()
        all_keys.update(cpi_keys)

    all_keys = sorted(all_keys)

    aggregated_data = aggregate_stats(args.folder, BASE_KEYS)

    for run, data in aggregated_data.items():
        print(f"\n[{run}]")
        for key in all_keys:
            print(f"{key}: {data.get(key, 'N/A')}")

    output_file = os.path.join(args.folder, "data.txt")
    save_data(aggregated_data, output_file, all_keys)
    print(f"\nAggregated data saved to: {output_file}")

if __name__ == "__main__":
    main()
