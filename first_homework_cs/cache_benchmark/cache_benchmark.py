"""
A simple run script using a specialized CHI cache hierarchy.
This script runs a simple test with a linear generator.

> gem5 run-test.py
"""


from gem5.components.boards.test_board import TestBoard
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.linear_generator import LinearGenerator
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes
from gem5.simulate.simulator import Simulator
from gem5.resources.resource import CustomResource
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import PrivateL1CacheHierarchy

from two_level_cache import PrivateL1L2Hierarchy
import argparse


# Argument parser
parser = argparse.ArgumentParser(description="Cache Benchmark Arguments")
parser.add_argument("--l1_size", type=str, default="128KiB", help="L1 cache size")
parser.add_argument("--l2_size", type=str, default="512KiB", help="L2 cache size")
parser.add_argument("--l1_assoc", type=int, default=16, help="L1 cache associativity")
parser.add_argument("--l2_assoc", type=int, default=16, help="L2 cache associativity")
parser.add_argument("--mult_version", type=int, default=1, help="1 -- iijjkk version, 2 -- kkjjii version, 3 -- kkiijj version")


args = parser.parse_args()

cpu_type = CPUTypes.TIMING
processor = SimpleProcessor(cpu_type=cpu_type, isa=ISA.X86, num_cores=1)


board = SimpleBoard(
    processor=processor,
    cache_hierarchy=PrivateL1L2Hierarchy(
        l1d_size=args.l1_size,
        l1d_assoc=args.l1_assoc,
        l1i_size=args.l1_size,
        l1i_assoc=args.l1_assoc,
        l2_size=args.l2_size,
        l2_assoc=args.l2_assoc,
    ),
    memory=SingleChannelDDR3_1600(size="2GB"),
    clk_freq="3GHz",
)

# Set the workload.
binary = CustomResource("../workload/MatMult/mat_mult" + str(args.mult_version) + ".bin")
board.set_se_binary_workload(binary)


sim = Simulator(board)
sim.run()