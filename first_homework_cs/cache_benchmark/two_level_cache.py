"""
This module contains a three-level cache hierarchy with private L1 caches,
private L2 caches, and a shared L3 cache.
"""

from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import (
    AbstractClassicCacheHierarchy,
)

from gem5.components.cachehierarchies.classic.caches.l2cache import L2Cache
from gem5.components.cachehierarchies.classic.caches.mmu_cache import MMUCache

from gem5.isas import ISA

from m5.objects import (
    BadAddr,
    Cache,
    L2XBar,
    SystemXBar,
    BasePrefetcher,
    Cache,
    StridePrefetcher,
)


class PrivateL1L2Hierarchy(AbstractClassicCacheHierarchy):

    def __init__(
        self,
        l1d_size,
        l1i_size,
        l2_size,
        l1d_assoc,
        l1i_assoc,
        l2_assoc,
    ):
        AbstractClassicCacheHierarchy.__init__(self)

        # Save the sizes to use later. We have to use leading underscores
        # because the SimObject (SubSystem) does not have these attributes as
        # parameters.
        self._l1d_size = l1d_size
        self._l1i_size = l1i_size
        self._l2_size = l2_size
        self._l1d_assoc = l1d_assoc
        self._l1i_assoc = l1i_assoc
        self._l2_assoc = l2_assoc

        ## define the interconnects with the system
        # the block size is 64 bytes, therefore the width is 64
        self.membus = SystemXBar(width=64)
        # For FS mode
        self.membus.badaddr_responder = BadAddr()
        self.membus.default = self.membus.badaddr_responder.pio

    ## helper functions to get the ports
    def get_mem_side_port(self): 
        """Returns the memory side port of the memory bus."""
        return self.membus.mem_side_ports
    
    def get_cpu_side_port(self):
        """Returns the CPU side port of the memory bus."""
        return self.membus.cpu_side_ports
    
    # build the cache hierarchy 
    def incorporate_cache(self, board):
        # Connect the system port to the memory bus cpu side ports 
        board.connect_system_port(self.membus.cpu_side_ports)
        
        # Connect the memory system to the memory port on the board.
        for _, port in board.get_memory().get_mem_ports():
            self.membus.mem_side_ports = port

        # 1. create the L1 level with L1D and L1I caches
        # 1a. create the L1D cache
        self.l1_dcache = myCustomCache(size=self._l1d_size, assoc=self._l1d_assoc, tag_latency=1, data_latency=1, response_latency=1, mshrs=16)
        # 1b. create the L1I cache
        self.l1_icache = myCustomCache(size=self._l1i_size, assoc=self._l1i_assoc, tag_latency=1, data_latency=1, response_latency=1, mshrs=16)
        # 1c. connect the L1D and L1I caches to the cpu 
        core = board.get_processor().get_cores()[0]
        core.connect_icache(self.l1_icache.cpu_side)
        core.connect_dcache(self.l1_dcache.cpu_side)
        # 2. create the L2 level
        # 2a. create the L2 cache
        self.l2_cache = myCustomCache(size=self._l2_size, assoc=self._l2_assoc, tag_latency=10, data_latency=10, response_latency=10, mshrs=20)

        # 2b. create the L2 xbar
        self.l2_xbar = L2XBar()

        # 2c. connect the L1D and L1I caches to the L2 cache
        self.l2_xbar.cpu_side_ports = self.l1_dcache.mem_side
        self.l2_xbar.cpu_side_ports = self.l1_icache.mem_side
        # 2d. connect the L2 cache to the L2 xbar
        self.l2_cache.cpu_side = self.l2_xbar.mem_side_ports
        #3. connect the L2 cache to the memory bus
        self.l2_cache.mem_side = self.membus.cpu_side_ports
        
        # Page table walker caches
        self.iptw_cache = MMUCache(size="8KiB", writeback_clean=False)
        self.dptw_cache = MMUCache(size="8KiB", writeback_clean=False)
        ## interface to processor 
        core.connect_walker_ports(
            self.iptw_cache.cpu_side, self.dptw_cache.cpu_side
        )
        ## interface to memory bus
        self.iptw_cache.mem_side = self.l2_xbar.cpu_side_ports
        self.dptw_cache.mem_side = self.l2_xbar.cpu_side_ports


        # connect the interrput ports 
        if board.get_processor().get_isa() == ISA.X86:
            int_req_port = self.membus.mem_side_ports
            int_resp_port = self.membus.cpu_side_ports
            core.connect_interrupt(int_req_port, int_resp_port)
        else:
            core.connect_interrupt()       
        
        if board.has_coherent_io():
            self._setup_io_cache(board)


    def _setup_io_cache(self, board: AbstractBoard) -> None:
        """Create a cache for coherent I/O connections"""
        self.iocache = Cache(
            assoc=8,
            tag_latency=50,
            data_latency=50,
            response_latency=50,
            mshrs=20,
            size="1kB",
            tgts_per_mshr=12,
            addr_ranges=board.mem_ranges,
        )
        self.iocache.mem_side = self.membus.cpu_side_ports
        self.iocache.cpu_side = board.get_mem_side_coherent_io_port()


# https://github.com/gem5/gem5/tree/stable/src/mem/cache/Cache.py
class myCustomCache(Cache):
    def __init__(self, size, assoc, tag_latency, data_latency, response_latency, mshrs, ):
        super().__init__() # always call the parent class constructor
        self.size = size
        self.assoc = assoc
        # tag lookup latency
        self.tag_latency = tag_latency
        # data access latency
        self.data_latency = data_latency
        # response latency - time to send response when a miss occurs
        self.response_latency = response_latency
        # number of MSHRs -> MISS status holding registers hardware structure for tracking outstanding misses
        self.mshrs = mshrs
        self.tgts_per_mshr = 12 
        self.writeback_clean = False
        self.clusivity = "mostly_incl"
        self.prefetcher = StridePrefetcher()
