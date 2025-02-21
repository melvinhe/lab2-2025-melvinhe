import yaml
import numpy as np
import os

from cache import Cache, CacheAssoc
from pathlib import Path
from typing import Union

arch_file = {
'architecture': {'version': 0.3, 'subtree': [{
    'name': 'system',
    'attributes': {'technology': '45nm'},
    'local': [{'name': 'private_cache',
               'class': 'simple_write_through_dcache',
               'attributes': {
                   'cache_size': 256,
                   'cache_block_size': 4,
                   'cache_associativity': 2,
                   'cache_datawidth': 8,
                   'DRAM_width': 64,
                   'DRAM_type': 'LPDDR4'}}]}]}}

cache_file = {
    'compound_components': {
        'version': 0.3,
        'classes': [{
            'name': 'simple_write_through_dcache',
            'attributes': {
                'technology': 'must_specify',
                'cache_size': 'must_specify',
                'cache_datawidth': 'must_specify',
                'cache_block_size': 'must_specify',
                'cache_associativity': 'must_specify',
                'DRAM_width': 'must_specify',
                'DRAM_type': 'must_specify'},
            'subcomponents': [{
                'name': 'cache',
                'class': 'SRAM',
                'attributes': {
                    'technology': 'technology',
                    'cache_type': 'dcache',
                    'size': 'cache_size',
                    'associativity': 'cache_associativity',
                    'block_size': 'cache_block_size',
                    'datawidth': 'cache_datawidth',
                    'tag_size': 64, 'n_rw_ports': 1,}}, {
                'name': 'DRAM',
                'class': 'DRAM',
                'attributes': {
                    'technology': 'technology',
                    'type': 'DRAM_type',
                    'width': 'DRAM_width'}}],
            'actions': [{
                'name': 'read_hit',
                'subcomponents': [{
                    'name': 'cache',
                    'actions': [{'name': 'read'}]}]}, {
                'name': 'write_hit',
                'subcomponents': [{
                    'name': 'DRAM', 'actions': [{'name': 'write'}]}, {
                    'name': 'cache',
                    'actions': [{'name': 'write'}]}]}, {
                'name': 'read_miss',
                'subcomponents': [{
                    'name': 'cache',
                    'actions': [{'name': 'read'}]}, {
                    'name': 'DRAM', 'actions': [{'name': 'read'}]}]}, {
                'name': 'write_miss',
                'subcomponents': [{
                    'name': 'DRAM', 'actions': [{'name': 'write'}]}]}]}]}}


action_count_file = {'action_counts':
                         {'version': 0.3,
                          'local': [{
                              'name': 'system.private_cache',
                              }]}}


class CacheProfiler(object):
    def __init__(self,
                 cache: Union[Cache, CacheAssoc],
                 # cache_size,
                 # cache_block_size,
                 # cache_associativity,
                 cache_datawidth=32,
                 DRAM_width=64,
                 DRAM_type='LPDDR4',
                 tag_size=64,
                 n_rd_ports=1,
                 n_wr_ports=1,
                 n_rdwr_ports=1,
                 n_banks=1,
                 ):
        self.arch = arch_file
        self.cache = cache_file
        self.action_count = action_count_file
        self.base_dir = Path(os.getcwd())
        cache_size = 2 ** cache.log_size
        cache_block_size = cache.words_per_line
        if hasattr(cache, 'num_ways'):
            cache_associativity = cache.num_ways
        else:
            cache_associativity = 1

        self.run_dir = self.base_dir/'profiles'/f"logsz{cache.log_size}" \
                                                f"_wpl{cache_block_size}" \
                                                f"_asso{cache_associativity}"

        os.makedirs(self.run_dir, exist_ok=True)

        self.arch['architecture']['subtree'][0]['local'][0]['attributes'][
            'cache_size'] = cache_size
        self.arch['architecture']['subtree'][0]['local'][0]['attributes'][
            'cache_block_size'] = cache_block_size
        self.arch['architecture']['subtree'][0]['local'][0]['attributes'][
            'cache_associativity'] = cache_associativity
        self.arch['architecture']['subtree'][0]['local'][0]['attributes'][
            'cache_datawidth'] = cache_datawidth
        self.arch['architecture']['subtree'][0]['local'][0]['attributes'][
            'DRAM_width'] = DRAM_width
        self.arch['architecture']['subtree'][0]['local'][0]['attributes'][
            'DRAM_type'] = DRAM_type

        self.cache['compound_components']['classes'][0][
            'subcomponents'][0]['attributes']['tag_size'] = tag_size
        self.cache['compound_components']['classes'][0][
            'subcomponents'][0]['attributes']['n_rd_ports'] = n_rd_ports
        self.cache['compound_components']['classes'][0][
            'subcomponents'][0]['attributes']['n_wr_ports'] = n_wr_ports
        self.cache['compound_components']['classes'][0][
            'subcomponents'][0]['attributes']['n_rw_ports'] = n_rdwr_ports
        self.cache['compound_components']['classes'][0][
            'subcomponents'][0]['attributes']['n_banks'] = n_banks

        self.cache['compound_components']['classes'][0][
            'subcomponents'][0]['attributes']['width'] = cache.words_per_line * cache_datawidth
        self.cache['compound_components']['classes'][0][
            'subcomponents'][0]['attributes']['depth'] = cache_size * cache_datawidth // (cache.words_per_line * cache_datawidth)

        with open(self.run_dir/'arch.yaml', 'w') as wfid:
            yaml.safe_dump(self.arch, wfid)

        with open(self.run_dir/'cache.yaml', 'w') as wfid:
            yaml.safe_dump(self.cache, wfid)

    def profile(self, action_count):
        actions = [{
            'name': 'read_miss',
            'counts': action_count['read_miss']}, {
            'name': 'read_hit',
            'counts': action_count['read_hit']}, {
            'name': 'write_miss',
            'counts': action_count['write_miss']}, {
            'name': 'write_hit',
            'counts': action_count['write_hit']}
        ]
        self.action_count['action_counts']['local'][0][
            'action_counts'] = actions

        with open(self.run_dir/'action_counts.yaml', 'w') as wfid:
            yaml.safe_dump(self.action_count, wfid)

        cwd = self.run_dir
        cmd = 'accelergy arch.yaml cache.yaml action_counts.yaml -v > accelergy.log 2>&1'

        os.chdir(cwd)
        os.system(cmd)
        os.chdir(self.base_dir)

        with open(self.run_dir/'energy_estimation.yaml', 'r') as rfid:
            results = yaml.safe_load(rfid)
            energy = results['energy_estimation']['components'][0]['energy']

        with open(self.run_dir/'ART.yaml', 'r') as rfid:
            results = yaml.safe_load(rfid)
            area = results['ART']['tables'][0]['area']

        return {'energy': energy, 'area': area}


if __name__ == '__main__':
    from cache import Cache, CacheAssoc
    cache_a = CacheAssoc(log_size=10, words_per_line=8, num_ways=2)
    profiler = CacheProfiler(cache_a)
    actions = {
        'read_miss': 100,
        'read_hit': 100,
        'write_miss': 100,
        'write_hit': 100,
    }

    res = profiler.profile(actions)

    print(res)
