import numpy as np
import math

def mask(n, bits):
    return n & ((1<<bits)-1)

# Direct Mapped, Write Through, No Write Allocate
class Cache(object):
    def __init__(self, log_size=11, words_per_line=4):
        self.log_size = log_size
        self.words_per_line = words_per_line
        self.log_num_lines = log_size - int(math.log(words_per_line,2))

        self.tags = -1*np.ones(1<<self.log_num_lines).astype(np.int32)
        self.wr_hit = 0
        self.wr_miss = 0

        self.rd_hit = 0
        self.rd_miss = 0

    def load(self, addr):
        addr_index = addr >> int(math.log(self.words_per_line,2))
        line_index = mask(addr_index, self.log_num_lines)
        tag = (addr >> self.log_size)
        #if self.tags[line_index] == -1:
        #    self.rd_miss += 1
        if self.tags[line_index] == tag:
            self.rd_hit += 1
            # print("Cache hit!", addr, line_index, tag)
        else:
            self.rd_miss += 1
            self.tags[line_index] = tag
            # print("Cache miss!", addr, line_index, tag)

    def store(self, addr):
        addr_index = addr >> int(math.log(self.words_per_line,2))
        line_index = mask(addr_index, self.log_num_lines)
        tag = (addr >> self.log_size)
        if self.tags[line_index] == tag:
            self.wr_hit += 1
            # print("Write hit!", addr, line_index, tag)
        else:
            self.wr_miss += 1
            # print("Write miss!", addr, line_index, tag)
        #    self.tags[line_index] = tag

    def print_stats(self):
        print("Cache Statistics:")
        print("cache rd: %d" % self.rd_hit)
        print("cache wr: %d" % self.wr_hit)
        print("mem rd: %d" % self.rd_miss)
        print("mem wr: %d" % (self.wr_miss + self.wr_hit))

    @property
    def stats(self) -> dict:
        return {
            'read_miss': self.rd_miss,
            'read_hit': self.rd_hit,
            'write_miss': self.wr_miss,
            'write_hit': self.wr_hit,
        }

# Associative Cache, Bit-PLRU, Write Through, No Write Allocate
class CacheAssoc(object):
    def __init__(self, num_ways=2, log_size=11, words_per_line=4):
        self.log_size = log_size
        self.words_per_line = words_per_line
        self.log_num_lines = log_size - int(math.log(words_per_line,2)) - int(math.log(num_ways,2))
        self.num_ways = num_ways
        self.lru = np.zeros((1<<self.log_num_lines, num_ways)).astype(np.bool_)

        self.tags = -1*np.ones((1<<self.log_num_lines, num_ways)).astype(np.int32)
        self.wr_hit = 0
        self.wr_miss = 0
        self.rd_hit = 0
        self.rd_miss = 0

    """
    def load(self, addr):
        addr_index = addr >> (int(math.log(self.words_per_line,2)))
        line_index = mask(addr_index, self.log_num_lines)
        tag = addr >> (self.log_size - int(math.log(self.num_ways,2)))
        #if self.tags[line_index] == -1:
        #    self.rd_miss += 1
        if self.tags[line_index][0] == tag:
            self.rd_hit += 1
            self.lru[line_index] = 1
        elif self.tags[line_index][1] == tag:
            self.rd_hit += 1
            self.lru[line_index] = 0
        else:
            self.rd_miss += 1
            #self.tags[line_index] = tag
            if self.lru[line_index] == 0:
                self.lru[line_index] = 1
                self.tags[line_index][0] = tag
            else:
                self.lru[line_index] = 0
                self.tags[line_index][1] = tag    
    
    def store(self, addr):
        addr_index = addr >> (int(math.log(self.words_per_line,2)))
        line_index = mask(addr_index, self.log_num_lines)
        tag = addr >> (self.log_size - int(math.log(self.num_ways,2)))
        
        self.wr_miss += 1
        #if self.tags[line_index] == tag:
        #    self.tags[line_index] = tag
    """
    
    # Check if all LRU bits in a set are 1
    def lru_all_used(self, line_index):
        return np.all(self.lru[line_index])
        
    def load(self, addr):
        addr_index = addr >> (int(math.log(self.words_per_line,2)))
        line_index = mask(addr_index, self.log_num_lines)
        tag = addr >> (self.log_size - int(math.log(self.num_ways,2)))
        
        # Compare all tags in a set 
        hit = False
        for n in range(self.num_ways):
            if self.tags[line_index][n] == tag:
                hit = True
                n_hit = n
                break
                
        # If hit, update the LRU bits in this set
        if hit:
            self.rd_hit += 1
            self.lru[line_index][n_hit] = 1
            
            # If all LRU bits in this set are 1, set the rest to 0 except for this tag
            if self.lru_all_used(line_index):
                self.lru[line_index][:] = 0
                self.lru[line_index][n_hit] = 1
                
            # print("Cache hit!")
            # print(line_index, n_hit)
            # print(self.lru[line_index])
            
        # If miss, load to the LRU entry
        else:
            self.rd_miss += 1
            
            # search for the leftmost entry with LRU=0
            for n in range(self.num_ways):
                if self.lru[line_index][n] == 0:
                    self.tags[line_index][n] = tag
                    self.lru[line_index][n] = 1
                    n_loaded = n
                    break
                    
            # If all LRU bits in this set are 1, set the rest to 0 except for this tag
            if self.lru_all_used(line_index):
                self.lru[line_index][:] = 0
                self.lru[line_index][n_loaded] = 1
                
            # print("Cache miss!")
            # print(line_index, n_loaded)
            # print(self.lru[line_index])
            
    def store(self, addr):
        addr_index = addr >> (int(math.log(self.words_per_line,2)))
        line_index = mask(addr_index, self.log_num_lines)
        tag = addr >> (self.log_size - int(math.log(self.num_ways,2)))
        
        # Compare all tags in a set 
        hit = False
        for n in range(self.num_ways):
            if self.tags[line_index][n] == tag:
                hit = True
                n_hit = n
                break
                
        # If hit, update the LRU bits in this set
        if hit:
            self.wr_hit += 1
            self.lru[line_index][n_hit] = 1
            
            # If all LRU bits in this set are 1, set the rest to 0 except for this tag
            if self.lru_all_used(line_index):
                self.lru[line_index][:] = 0
                self.lru[line_index][n_hit] = 1
                
        # If miss, no write allocate - only write miss
        else:
            self.wr_miss += 1
    
    def print_stats(self):
        print("Cache Statistics:")
        print("cache rd: %d" % self.rd_hit)
        print("cache wr: %d" % self.wr_hit)
        print("mem rd: %d" % self.rd_miss)
        print("mem wr: %d" % (self.wr_miss + self.wr_hit))

    @property
    def stats(self) -> dict:
        return {
            'read_miss': self.rd_miss,
            'read_hit': self.rd_hit,
            'write_miss': self.wr_miss,
            'write_hit': self.wr_hit,
        }