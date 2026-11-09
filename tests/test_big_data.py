"""
Test Suite for Project B: Big Data Processing Lab.
Tests in-memory Pandas, Chunk-based streaming, MapReduce,
Spark runtime environment diagnostics, and on-demand benchmark generation.
"""

import tempfile
import os
import pytest
import numpy as np
import pandas as pd

from src.bigdata_engine import (
    run_pandas_processing, run_chunked_processing, run_mapreduce_processing,
    check_spark_environment, run_spark_processing, generate_temporary_benchmark_dataset
)

@pytest.fixture
def benchmark_sample():
    return generate_temporary_benchmark_dataset(n_records=2000)

def test_pandas_processing(benchmark_sample):
    p_res, p_time, p_mem = run_pandas_processing(benchmark_sample, group_col='platform')
    assert len(p_res) == 5
    assert p_time >= 0.0
    assert 'spend' in p_res.columns

def test_chunked_stream_processing(benchmark_sample):
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tf:
        temp_path = tf.name
        benchmark_sample.to_csv(temp_path, index=False)
        
    try:
        c_res, c_time, c_mem, c_rows = run_chunked_processing(temp_path, chunk_size=500, group_col='platform')
        assert c_rows == len(benchmark_sample)
        assert len(c_res) == 5
        assert np.isclose(c_res['spend'].sum(), benchmark_sample['spend'].sum(), rtol=1e-3)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_mapreduce_streaming_consistency(benchmark_sample):
    p_res, _, _ = run_pandas_processing(benchmark_sample, group_col='platform')
    m_res, m_time, m_mem = run_mapreduce_processing(benchmark_sample, group_col='platform', chunk_size=500)
    
    assert len(m_res) == len(p_res)
    assert m_res['clicks'].sum() == p_res['clicks'].sum()
    assert m_res['impressions'].sum() == p_res['impressions'].sum()
    assert np.isclose(m_res['spend'].sum(), p_res['spend'].sum(), rtol=1e-4)

def test_spark_runtime_environment_detection():
    is_avail, msg = check_spark_environment()
    assert isinstance(is_avail, bool)
    assert isinstance(msg, str)

def test_spark_honest_diagnostic_handling(benchmark_sample):
    sp_res, sp_time, sp_mem, sp_meta = run_spark_processing(benchmark_sample)
    if not sp_meta['available']:
        assert sp_res is None
        assert sp_meta['status'] in ('UNAVAILABLE', 'FAILED')
        assert 'Java' in sp_meta['diagnostic'] or 'pyspark' in sp_meta['diagnostic']

def test_on_demand_benchmark_generation():
    df = generate_temporary_benchmark_dataset(n_records=1000)
    assert len(df) == 1000
    assert 'platform' in df.columns
    assert 'spend' in df.columns

