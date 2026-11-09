"""
Big Data Processing Lab Engine.
Provides genuine implementations across processing paradigms:
1. In-Memory Pandas Vectorization
2. Chunk-Based Stream Processing (Configurable chunksize)
3. Streaming MapReduce (Mapper, Shuffle/Partition, Reducer)
4. Apache Spark Integration (Runtime Java & PySpark detection with honest diagnostics)
5. On-Demand Temporary Dataset Generation for Scalability Benchmarking
"""

import os
import time
import shutil
import tracemalloc
from collections import defaultdict
from typing import Dict, Any, Tuple, Optional, List, Callable
import numpy as np
import pandas as pd

from src.advertising_analytics import safe_divide

def run_pandas_processing(df: pd.DataFrame, group_col: str = 'platform') -> Tuple[pd.DataFrame, float, float]:
    """
    Executes in-memory vectorized aggregation using Pandas.
    Returns: (result_df, execution_time_sec, memory_peak_mb)
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    
    col_dict = {
        'impressions': 'sum',
        'clicks': 'sum',
        'spend': 'sum',
        'conversions': 'sum',
        'revenue': 'sum'
    }
    actual_agg = {c: col_dict[c] for c in col_dict if c in df.columns}
    if not actual_agg:
        actual_agg = {df.columns[1]: 'count'} if len(df.columns) > 1 else {df.columns[0]: 'count'}
        
    agg_df = df.groupby(group_col, as_index=False).agg(actual_agg)
    
    if 'clicks' in agg_df.columns and 'impressions' in agg_df.columns:
        agg_df['CTR'] = safe_divide(agg_df['clicks'] * 100.0, agg_df['impressions'])
    if 'spend' in agg_df.columns and 'clicks' in agg_df.columns:
        agg_df['CPC'] = safe_divide(agg_df['spend'], agg_df['clicks'])
    if 'spend' in agg_df.columns and 'conversions' in agg_df.columns:
        agg_df['CPA'] = safe_divide(agg_df['spend'], agg_df['conversions'])
    if 'revenue' in agg_df.columns and 'spend' in agg_df.columns:
        agg_df['ROAS'] = safe_divide(agg_df['revenue'], agg_df['spend'])
        
    t1 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return agg_df.sort_values(by=group_col).reset_index(drop=True), t1 - t0, peak / (1024 * 1024)


def run_chunked_processing(file_path_or_buffer,
                           chunk_size: int = 10000,
                           group_col: str = 'platform',
                           progress_callback: Optional[Callable[[int], None]] = None) -> Tuple[pd.DataFrame, float, float, int]:
    """
    Processes large datasets chunk-by-chunk without loading the entire file into memory at once.
    Returns: (result_df, execution_time_sec, memory_peak_mb, total_rows_processed)
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    
    accumulators = defaultdict(lambda: [0, 0, 0.0, 0, 0.0, 0])
    total_rows = 0
    
    # Read in chunks
    for chunk in pd.read_csv(file_path_or_buffer, chunksize=chunk_size):
        total_rows += len(chunk)
        if group_col not in chunk.columns:
            continue
            
        agg_dict = {
            c: 'sum' for c in ['impressions', 'clicks', 'spend', 'conversions', 'revenue'] if c in chunk.columns
        }
        if not agg_dict:
            continue
            
        grp = chunk.groupby(group_col).agg(agg_dict)
        
        for key, row in grp.iterrows():
            acc = accumulators[key]
            acc[0] += int(row.get('impressions', 0)) if 'impressions' in chunk.columns else 0
            acc[1] += int(row.get('clicks', 0)) if 'clicks' in chunk.columns else 0
            acc[2] += float(row.get('spend', 0.0)) if 'spend' in chunk.columns else 0.0
            acc[3] += int(row.get('conversions', 0)) if 'conversions' in chunk.columns else 0
            acc[4] += float(row.get('revenue', 0.0)) if 'revenue' in chunk.columns else 0.0
            acc[5] += 1
            
        if progress_callback:
            progress_callback(total_rows)
            
    # Compile final result
    rows = []
    for k, vals in sorted(accumulators.items()):
        imp, clk, spd, cnv, rev, cnt = vals
        rows.append({
            group_col: k,
            'impressions': imp,
            'clicks': clk,
            'spend': round(spd, 2),
            'conversions': cnv,
            'revenue': round(rev, 2),
            'CTR': safe_divide(clk * 100.0, imp),
            'CPC': safe_divide(spd, clk),
            'CPA': safe_divide(spd, cnv),
            'ROAS': safe_divide(rev, spd)
        })
        
    t1 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return pd.DataFrame(rows), t1 - t0, peak / (1024 * 1024), total_rows


def run_mapreduce_processing(df: pd.DataFrame,
                             group_col: str = 'platform',
                             chunk_size: int = 50000) -> Tuple[pd.DataFrame, float, float]:
    """
    Executes platform or campaign aggregation using MapReduce streaming primitives:
    1. Mapper: (key, [imp, clk, spd, cnv, rev])
    2. Shuffle: Partition into key buckets
    3. Reducer: Aggregate sums and compute final KPIs
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    
    partitions = defaultdict(lambda: [0, 0, 0.0, 0, 0.0, 0])
    n_rows = len(df)
    
    key_arr = df[group_col].astype(str).to_numpy()
    imp_arr = df['impressions'].to_numpy() if 'impressions' in df.columns else np.zeros(n_rows)
    clk_arr = df['clicks'].to_numpy() if 'clicks' in df.columns else np.zeros(n_rows)
    spd_arr = df['spend'].to_numpy() if 'spend' in df.columns else np.zeros(n_rows)
    cnv_arr = df['conversions'].to_numpy() if 'conversions' in df.columns else np.zeros(n_rows)
    rev_arr = df['revenue'].to_numpy() if 'revenue' in df.columns else np.zeros(n_rows)
    
    for i in range(0, n_rows, chunk_size):
        end_idx = min(i + chunk_size, n_rows)
        sub_keys = key_arr[i:end_idx]
        sub_imp = imp_arr[i:end_idx]
        sub_clk = clk_arr[i:end_idx]
        sub_spd = spd_arr[i:end_idx]
        sub_cnv = cnv_arr[i:end_idx]
        sub_rev = rev_arr[i:end_idx]
        
        for j in range(len(sub_keys)):
            k = sub_keys[j]
            acc = partitions[k]
            acc[0] += int(sub_imp[j])
            acc[1] += int(sub_clk[j])
            acc[2] += float(sub_spd[j])
            acc[3] += int(sub_cnv[j])
            acc[4] += float(sub_rev[j])
            acc[5] += 1
            
    # Reducer
    rows = []
    for k, vals in sorted(partitions.items()):
        imp, clk, spd, cnv, rev, cnt = vals
        rows.append({
            group_col: k,
            'impressions': imp,
            'clicks': clk,
            'spend': round(spd, 2),
            'conversions': cnv,
            'revenue': round(rev, 2),
            'CTR': safe_divide(clk * 100.0, imp),
            'CPC': safe_divide(spd, clk),
            'CPA': safe_divide(spd, cnv),
            'ROAS': safe_divide(rev, spd)
        })
        
    t1 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return pd.DataFrame(rows), t1 - t0, peak / (1024 * 1024)


def check_spark_environment() -> Tuple[bool, str]:
    """Detects runtime Java and PySpark availability."""
    java_bin = shutil.which('java')
    if not java_bin:
        return False, "Java Development Kit (JDK/JRE) not detected in system PATH. Apache Spark requires Java 8/11/17 runtime."
    try:
        import pyspark
        return True, f"PySpark {pyspark.__version__} and Java ({java_bin}) available."
    except ImportError:
        return False, "pyspark package is not installed in the active Python environment."
    except Exception as e:
        return False, f"Spark environment check error: {str(e)}"


def run_spark_processing(df: pd.DataFrame, group_col: str = 'platform') -> Tuple[Optional[pd.DataFrame], float, float, Dict[str, Any]]:
    """Executes Apache Spark aggregation if available; otherwise returns honest diagnostic."""
    is_avail, msg = check_spark_environment()
    if not is_avail:
        return None, 0.0, 0.0, {'available': False, 'diagnostic': msg, 'status': 'UNAVAILABLE'}
        
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
        
        spark = SparkSession.builder.appName("AdAnalyticsSpark").master("local[*]").getOrCreate()
        spark_df = spark.createDataFrame(df)
        
        agg = spark_df.groupBy(group_col).agg(
            F.sum("impressions").alias("impressions"),
            F.sum("clicks").alias("clicks"),
            F.sum("spend").alias("spend"),
            F.sum("conversions").alias("conversions"),
            F.sum("revenue").alias("revenue")
        )
        res_df = agg.toPandas()
        spark.stop()
        
        t1 = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return res_df, t1 - t0, peak / (1024 * 1024), {'available': True, 'diagnostic': 'Spark execution successful', 'status': 'SUCCESS'}
    except Exception as ex:
        tracemalloc.stop()
        return None, 0.0, 0.0, {'available': False, 'diagnostic': f"Spark execution failed: {str(ex)}", 'status': 'FAILED'}


def generate_temporary_benchmark_dataset(n_records: int = 25000) -> pd.DataFrame:
    """
    Generates an in-memory synthetic dataset strictly for on-demand scalability testing.
    Labeled as benchmark data; no persistent disk footprint required.
    """
    from src.dataset_generator import generate_advertising_data
    return generate_advertising_data(n_records=n_records, seed=42)
