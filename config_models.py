from typing import List, Optional
from pydantic import BaseModel, Field
from itertools import product
from dataclasses import dataclass
import json


@dataclass
class CacheInstance:
    cache_size: Optional[int] = None
    cache_block_size: Optional[int] = None
    associativity: Optional[int] = None
    replacement: Optional[str] = None
    
    def __repr__(self):
        return (f"CacheInstance(cache_size={self.cache_size}, "
                f"cache_block_size={self.cache_block_size}, "
                f"associativity={self.associativity}, "
                f"replacement='{self.replacement}')")
    
    def to_cli_args(self, prefix: str) -> List[str]:
        args = []
        if self.cache_size is not None:
            args.append(f'"perf_model/{prefix}/cache_size={self.cache_size}"')
        if self.cache_block_size is not None:
            args.append(f'"perf_model/{prefix}/cache_block_size={self.cache_block_size}"')
        if self.associativity is not None:
            args.append(f'"perf_model/{prefix}/associativity={self.associativity}"')
        if self.replacement is not None:
            args.append(f'"perf_model/{prefix}/replacement={self.replacement}"')
        return args


@dataclass
class TLBInstance:
    entries: Optional[int] = None
    associativity: Optional[int] = None
    page_size: Optional[int] = None
    
    def __repr__(self):
        return (f"TLBInstance(entries={self.entries}, "
                f"associativity={self.associativity}, "
                f"page_size={self.page_size})")
    
    def to_cli_args(self, prefix: str) -> List[str]:
        args = []
        if self.entries is not None:
            args.append(f'"perf_model/{prefix}/entries={self.entries}"')
        if self.associativity is not None:
            args.append(f'"perf_model/{prefix}/associativity={self.associativity}"')
        if self.page_size is not None:
            args.append(f'"perf_model/{prefix}/page_size={self.page_size}"')
        return args


@dataclass
class ConfigurationSet:
    l1_icache: Optional[CacheInstance] = None
    l1_dcache: Optional[CacheInstance] = None
    l2_cache: Optional[CacheInstance] = None
    l3_cache: Optional[CacheInstance] = None
    l4_cache: Optional[CacheInstance] = None
    itlb: Optional[TLBInstance] = None
    dtlb: Optional[TLBInstance] = None
    
    def __repr__(self):
        parts = []
        if self.l1_icache:
            parts.append(f"l1_icache={self.l1_icache}")
        if self.l1_dcache:
            parts.append(f"l1_dcache={self.l1_dcache}")
        if self.l2_cache:
            parts.append(f"l2_cache={self.l2_cache}")
        if self.l3_cache:
            parts.append(f"l3_cache={self.l3_cache}")
        if self.l4_cache:
            parts.append(f"l4_cache={self.l4_cache}")
        if self.itlb:
            parts.append(f"itlb={self.itlb}")
        if self.dtlb:
            parts.append(f"dtlb={self.dtlb}")
        return f"ConfigurationSet({', '.join(parts)})"
    
    def to_cli_args(self) -> List[str]:
        args = []
        if self.itlb:
            args.extend(self.itlb.to_cli_args("itlb"))
        if self.dtlb:
            args.extend(self.dtlb.to_cli_args("dtlb"))
        if self.l1_icache:
            args.extend(self.l1_icache.to_cli_args("l1_icache"))
        if self.l1_dcache:
            args.extend(self.l1_dcache.to_cli_args("l1_dcache"))
        if self.l2_cache:
            args.extend(self.l2_cache.to_cli_args("l2_cache"))
        if self.l3_cache:
            args.extend(self.l3_cache.to_cli_args("l3_cache"))
        if self.l4_cache:
            args.extend(self.l4_cache.to_cli_args("l4_cache"))
        return args


class CacheConfig(BaseModel):
    cache_size: List[int] = Field(default_factory=list)
    cache_block_size: List[int] = Field(default_factory=list)
    associativity: List[int] = Field(default_factory=list)
    replacement: List[str] = Field(default_factory=list)
    
    def generate_combinations(self) -> List[CacheInstance]:
        if not any([self.cache_size, self.cache_block_size, self.associativity, self.replacement]):
            return []
        
        cache_sizes = self.cache_size if self.cache_size else [None]
        block_sizes = self.cache_block_size if self.cache_block_size else [None]
        associativities = self.associativity if self.associativity else [None]
        replacements = self.replacement if self.replacement else [None]
        
        return [CacheInstance(*combo) 
                for combo in product(cache_sizes, block_sizes, associativities, replacements)]


class TLBConfig(BaseModel):
    entries: List[int] = Field(default_factory=list)
    associativity: List[int] = Field(default_factory=list)
    page_size: List[int] = Field(default_factory=list)
    
    def generate_combinations(self) -> List[TLBInstance]:
        if not any([self.entries, self.associativity, self.page_size]):
            return []
        
        entries_list = self.entries if self.entries else [None]
        associativities = self.associativity if self.associativity else [None]
        page_sizes = self.page_size if self.page_size else [None]
        
        return [TLBInstance(*combo) 
                for combo in product(entries_list, associativities, page_sizes)]


class CachesConfig(BaseModel):
    l1_icache: CacheConfig = Field(default_factory=CacheConfig)
    l1_dcache: CacheConfig = Field(default_factory=CacheConfig)
    l2_cache: CacheConfig = Field(default_factory=CacheConfig)
    l3_cache: CacheConfig = Field(default_factory=CacheConfig)
    l4_cache: CacheConfig = Field(default_factory=CacheConfig)


class TLBsConfig(BaseModel):
    itlb: TLBConfig = Field(default_factory=TLBConfig)
    dtlb: TLBConfig = Field(default_factory=TLBConfig)


class ExplorerConfig(BaseModel):
    caches: CachesConfig = Field(default_factory=CachesConfig)
    TLBs: TLBsConfig = Field(default_factory=TLBsConfig)

    @classmethod
    def from_json_file(cls, filepath: str) -> 'ExplorerConfig':
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_json_file(self, filepath: str, indent: int = 4) -> None:
        with open(filepath, 'w') as f:
            f.write(self.model_dump_json(indent=indent))

    def to_dict(self) -> dict:
        return self.model_dump()
    
    def generate_all_configurations(self) -> List[ConfigurationSet]:
        l1_icache_combos = self.caches.l1_icache.generate_combinations() or [None]
        l1_dcache_combos = self.caches.l1_dcache.generate_combinations() or [None]
        l2_cache_combos = self.caches.l2_cache.generate_combinations() or [None]
        l3_cache_combos = self.caches.l3_cache.generate_combinations() or [None]
        l4_cache_combos = self.caches.l4_cache.generate_combinations() or [None]
        itlb_combos = self.TLBs.itlb.generate_combinations() or [None]
        dtlb_combos = self.TLBs.dtlb.generate_combinations() or [None]

        return [ConfigurationSet(
                    l1_icache=combo[0],
                    l1_dcache=combo[1],
                    l2_cache=combo[2],
                    l3_cache=combo[3],
                    l4_cache=combo[4],
                    itlb=combo[5],
                    dtlb=combo[6]
                )
                for combo in product(l1_icache_combos, l1_dcache_combos, l2_cache_combos,
                                    l3_cache_combos, l4_cache_combos, itlb_combos, dtlb_combos)]

class ADSEConfig(BaseModel):
    run_sniper_path: str = Field(default="")
    output_dir: str = Field(default="")
    cfgfile: str = Field(default="")
    benchmark_path: str = Field(default="")
    parameters: ExplorerConfig = Field(default_factory=ExplorerConfig)

    @classmethod
    def from_json_file(cls, filepath: str) -> 'ADSEConfig':
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_json_file(self, filepath: str, indent: int = 4) -> None:
        with open(filepath, 'w') as f:
            f.write(self.model_dump_json(indent=indent))

    def to_dict(self) -> dict:
        return self.model_dump()