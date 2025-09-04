"""
Performance Benchmarking Tests with Statistical Analysis
Comprehensive performance testing and statistical validation
"""

import pytest
import asyncio
import httpx
import time
import json
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from scipy import stats
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = None

@dataclass 
class BenchmarkResult:
    """Benchmark test result"""
    test_name: str
    metrics: List[PerformanceMetric]
    duration: float
    success_rate: float
    statistical_summary: Dict[str, float]

@pytest.mark.performance
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Comprehensive performance benchmarking with statistical analysis"""
    
    async def test_api_response_time_distribution(self, test_config, performance_tracker, statistical_validator):
        """Analyze API response time distribution with statistical rigor"""
        
        sample_size = 100  # Large sample for statistical significance
        endpoints = [
            '/health',
            '/api/v1/health', 
            '/',
            '/api/docs'
        ]
        
        all_response_times = []
        endpoint_performance = {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in endpoints:
                endpoint_times = []
                logger.info(f"Benchmarking endpoint: {endpoint}")
                
                for i in range(sample_size // len(endpoints)):  # Distribute samples across endpoints
                    start_time = time.perf_counter()
                    
                    try:
                        response = await client.get(f"{test_config['base_url']}{endpoint}")
                        response_time = time.perf_counter() - start_time
                        
                        if response.status_code == 200:
                            endpoint_times.append(response_time * 1000)  # Convert to milliseconds
                            all_response_times.append(response_time * 1000)
                            performance_tracker.add_metric('api_response_time', response_time * 1000)
                    
                    except Exception as e:
                        logger.warning(f"Request failed for {endpoint}: {e}")
                    
                    # Small delay to avoid overwhelming the server
                    await asyncio.sleep(0.01)
                
                if endpoint_times:
                    endpoint_performance[endpoint] = {
                        'mean': np.mean(endpoint_times),
                        'median': np.median(endpoint_times),
                        'std': np.std(endpoint_times),
                        'min': np.min(endpoint_times),
                        'max': np.max(endpoint_times),
                        'p95': np.percentile(endpoint_times, 95),
                        'p99': np.percentile(endpoint_times, 99),
                        'sample_size': len(endpoint_times)
                    }
        
        # Statistical analysis
        if all_response_times:
            response_times_array = np.array(all_response_times)
            
            # Test for normality (Shapiro-Wilk test)
            if len(all_response_times) <= 5000:  # Shapiro-Wilk limitation
                normality_stat, normality_p = stats.shapiro(response_times_array[:5000])
            else:
                # Use Kolmogorov-Smirnov test for larger samples
                normality_stat, normality_p = stats.kstest(response_times_array, 'norm')
            
            # Performance validation
            validation_result = statistical_validator.validate_performance(
                all_response_times, threshold=500.0, test_type='p95'  # 500ms P95 threshold
            )
            
            # Log comprehensive statistics
            logger.info("API Response Time Performance Analysis:")
            logger.info(f"  Sample size: {len(all_response_times)}")
            logger.info(f"  Mean: {np.mean(all_response_times):.2f}ms")
            logger.info(f"  Median: {np.median(all_response_times):.2f}ms") 
            logger.info(f"  Standard deviation: {np.std(all_response_times):.2f}ms")
            logger.info(f"  95th percentile: {np.percentile(all_response_times, 95):.2f}ms")
            logger.info(f"  99th percentile: {np.percentile(all_response_times, 99):.2f}ms")
            logger.info(f"  Min: {np.min(all_response_times):.2f}ms")
            logger.info(f"  Max: {np.max(all_response_times):.2f}ms")
            logger.info(f"  Normality test p-value: {normality_p:.4f}")
            
            # Endpoint-specific performance
            for endpoint, perf in endpoint_performance.items():
                logger.info(f"  {endpoint} - Mean: {perf['mean']:.2f}ms, P95: {perf['p95']:.2f}ms")
            
            # Assertions
            assert validation_result['valid'], f"API response time performance failed: {validation_result}"
            assert np.mean(all_response_times) < 200.0, f"Mean response time too high: {np.mean(all_response_times):.2f}ms"

    async def test_throughput_under_load(self, test_config, performance_tracker):
        """Test API throughput under various load levels"""
        
        load_levels = [1, 5, 10, 20]  # Concurrent requests
        duration_per_test = 30  # 30 seconds per load level
        
        throughput_results = {}
        
        for concurrent_users in load_levels:
            logger.info(f"Testing throughput with {concurrent_users} concurrent users")
            
            start_time = time.time()
            end_time = start_time + duration_per_test
            
            request_count = 0
            successful_requests = 0
            error_count = 0
            response_times = []
            
            async def make_requests():
                nonlocal request_count, successful_requests, error_count
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    while time.time() < end_time:
                        request_start = time.perf_counter()
                        request_count += 1
                        
                        try:
                            response = await client.get(f"{test_config['base_url']}/health")
                            request_time = time.perf_counter() - request_start
                            
                            if response.status_code == 200:
                                successful_requests += 1
                                response_times.append(request_time * 1000)
                            else:
                                error_count += 1
                        
                        except Exception as e:
                            error_count += 1
                            logger.debug(f"Request failed: {e}")
                        
                        # Brief pause between requests for this user
                        await asyncio.sleep(0.1)
            
            # Launch concurrent users
            tasks = [make_requests() for _ in range(concurrent_users)]
            await asyncio.gather(*tasks)
            
            actual_duration = time.time() - start_time
            throughput = successful_requests / actual_duration
            error_rate = error_count / request_count if request_count > 0 else 0
            
            throughput_results[concurrent_users] = {
                'throughput': throughput,
                'error_rate': error_rate,
                'avg_response_time': np.mean(response_times) if response_times else 0,
                'p95_response_time': np.percentile(response_times, 95) if response_times else 0,
                'total_requests': request_count,
                'successful_requests': successful_requests,
                'duration': actual_duration
            }
            
            performance_tracker.add_metric('throughput', throughput)
            performance_tracker.add_metric('error_rate', error_rate)
            
            logger.info(f"Load {concurrent_users} users - Throughput: {throughput:.2f} req/s, "
                       f"Error rate: {error_rate:.2%}, Avg response: {np.mean(response_times) if response_times else 0:.2f}ms")
            
            # Brief cooldown between load tests
            await asyncio.sleep(2)
        
        # Analyze throughput scaling
        logger.info("Throughput Scaling Analysis:")
        for users, results in throughput_results.items():
            logger.info(f"  {users} users: {results['throughput']:.2f} req/s, "
                       f"Error rate: {results['error_rate']:.2%}")
        
        # Validate that system can handle load
        max_throughput = max(result['throughput'] for result in throughput_results.values())
        min_error_rate = min(result['error_rate'] for result in throughput_results.values())
        
        assert max_throughput >= 10.0, f"Maximum throughput too low: {max_throughput:.2f} req/s"
        assert min_error_rate <= 0.05, f"Minimum error rate too high: {min_error_rate:.2%}"

    async def test_memory_and_cpu_usage(self, test_config, performance_tracker, system_monitor):
        """Test system resource usage under load"""
        
        # Baseline measurement
        baseline_stats = system_monitor.get_current_stats()
        baseline_memory = baseline_stats['memory'].used
        
        # Generate sustained load for resource measurement
        load_duration = 60  # 1 minute of sustained load
        concurrent_requests = 10
        
        resource_measurements = []
        
        async def generate_load():
            """Generate sustained load on the system"""
            async with httpx.AsyncClient(timeout=15.0) as client:
                end_time = time.time() + load_duration
                
                while time.time() < end_time:
                    try:
                        # Mix of different endpoints to simulate real usage
                        endpoints = ['/health', '/api/v1/health', '/']
                        endpoint = endpoints[int(time.time()) % len(endpoints)]
                        
                        await client.get(f"{test_config['base_url']}{endpoint}")
                        await asyncio.sleep(0.1)  # 10 requests per second per worker
                        
                    except Exception as e:
                        logger.debug(f"Load generation request failed: {e}")
        
        async def monitor_resources():
            """Monitor system resources during load test"""
            start_time = time.time()
            
            while time.time() - start_time < load_duration:
                current_stats = system_monitor.get_current_stats()
                
                measurement = {
                    'timestamp': time.time(),
                    'memory_used': current_stats['memory'].used,
                    'memory_percent': current_stats['memory'].percent,
                    'cpu_percent': current_stats['cpu'],
                    'memory_available': current_stats['memory'].available
                }
                
                resource_measurements.append(measurement)
                await asyncio.sleep(1)  # Measure every second
        
        # Start load generation and resource monitoring
        load_tasks = [generate_load() for _ in range(concurrent_requests)]
        monitor_task = monitor_resources()
        
        await asyncio.gather(monitor_task, *load_tasks)
        
        # Analyze resource usage
        if resource_measurements:
            memory_usage = [m['memory_used'] for m in resource_measurements]
            cpu_usage = [m['cpu_percent'] for m in resource_measurements]
            
            memory_increase = max(memory_usage) - baseline_memory
            avg_cpu_usage = np.mean(cpu_usage)
            max_cpu_usage = max(cpu_usage)
            
            performance_tracker.add_metric('memory_increase', memory_increase / (1024*1024))  # MB
            performance_tracker.add_metric('avg_cpu_usage', avg_cpu_usage)
            performance_tracker.add_metric('max_cpu_usage', max_cpu_usage)
            
            logger.info("Resource Usage Analysis:")
            logger.info(f"  Memory increase: {memory_increase / (1024*1024):.2f} MB")
            logger.info(f"  Average CPU usage: {avg_cpu_usage:.1f}%")
            logger.info(f"  Maximum CPU usage: {max_cpu_usage:.1f}%")
            logger.info(f"  Peak memory usage: {max(memory_usage) / (1024*1024*1024):.2f} GB")
            
            # Validate resource usage is reasonable
            assert memory_increase < 500 * 1024 * 1024, f"Memory increase too high: {memory_increase / (1024*1024):.2f} MB"
            assert avg_cpu_usage < 80.0, f"Average CPU usage too high: {avg_cpu_usage:.1f}%"

    async def test_database_performance(self, test_config, performance_tracker, statistical_validator):
        """Test database query performance"""
        
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        query_times = []
        connection_times = []
        
        # Test different types of queries
        test_queries = [
            "SELECT 1",  # Simple query
            "SELECT NOW()",  # Function query
            "SELECT COUNT(*) FROM information_schema.tables",  # Count query
            "SELECT table_name FROM information_schema.tables LIMIT 10"  # Data retrieval
        ]
        
        for i in range(50):  # 50 iterations for statistical significance
            # Test connection time
            conn_start = time.perf_counter()
            try:
                conn = psycopg2.connect(test_config['postgres_url'])
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                connection_time = time.perf_counter() - conn_start
                connection_times.append(connection_time * 1000)  # ms
                
                # Test query performance
                for query in test_queries:
                    query_start = time.perf_counter()
                    cursor.execute(query)
                    result = cursor.fetchall()
                    query_time = time.perf_counter() - query_start
                    query_times.append(query_time * 1000)  # ms
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                logger.error(f"Database performance test failed: {e}")
        
        # Statistical analysis
        if query_times and connection_times:
            # Validate query performance
            query_validation = statistical_validator.validate_performance(
                query_times, threshold=100.0, test_type='p95'  # 100ms P95 threshold
            )
            
            # Validate connection performance
            connection_validation = statistical_validator.validate_performance(
                connection_times, threshold=50.0, test_type='mean'  # 50ms mean threshold
            )
            
            performance_tracker.add_metric('db_query_time', np.mean(query_times))
            performance_tracker.add_metric('db_connection_time', np.mean(connection_times))
            
            logger.info("Database Performance Analysis:")
            logger.info(f"  Query times - Mean: {np.mean(query_times):.2f}ms, "
                       f"P95: {np.percentile(query_times, 95):.2f}ms")
            logger.info(f"  Connection times - Mean: {np.mean(connection_times):.2f}ms, "
                       f"P95: {np.percentile(connection_times, 95):.2f}ms")
            
            assert query_validation['valid'], f"Database query performance failed: {query_validation}"
            assert connection_validation['valid'], f"Database connection performance failed: {connection_validation}"

    async def test_cache_performance(self, test_config, performance_tracker):
        """Test Redis cache performance"""
        
        import redis
        
        cache_operations = []
        operation_types = ['set', 'get', 'delete', 'exists']
        
        r = redis.from_url(test_config['redis_url'])
        
        # Test different cache operations
        for i in range(100):  # 100 operations per type
            test_key = f"perf_test_key_{i}"
            test_value = f"performance_test_value_{i}_{'x' * 100}"  # 100+ char value
            
            for operation in operation_types:
                op_start = time.perf_counter()
                
                try:
                    if operation == 'set':
                        r.set(test_key, test_value, ex=60)  # 60 second expiry
                    elif operation == 'get':
                        r.get(test_key)
                    elif operation == 'exists':
                        r.exists(test_key)
                    elif operation == 'delete':
                        r.delete(test_key)
                    
                    operation_time = time.perf_counter() - op_start
                    cache_operations.append({
                        'operation': operation,
                        'time': operation_time * 1000,  # ms
                        'key': test_key
                    })
                    
                except Exception as e:
                    logger.error(f"Cache operation {operation} failed: {e}")
        
        # Analyze cache performance by operation type
        operation_stats = {}
        for op_type in operation_types:
            op_times = [op['time'] for op in cache_operations if op['operation'] == op_type]
            
            if op_times:
                operation_stats[op_type] = {
                    'mean': np.mean(op_times),
                    'p95': np.percentile(op_times, 95),
                    'min': np.min(op_times),
                    'max': np.max(op_times),
                    'count': len(op_times)
                }
                
                performance_tracker.add_metric(f'cache_{op_type}_time', np.mean(op_times))
        
        logger.info("Cache Performance Analysis:")
        for op_type, stats in operation_stats.items():
            logger.info(f"  {op_type.upper()} - Mean: {stats['mean']:.3f}ms, "
                       f"P95: {stats['p95']:.3f}ms, Samples: {stats['count']}")
        
        # Validate cache performance
        if operation_stats:
            # All operations should be very fast
            for op_type, stats in operation_stats.items():
                assert stats['mean'] < 10.0, f"Cache {op_type} operation too slow: {stats['mean']:.3f}ms"
                assert stats['p95'] < 20.0, f"Cache {op_type} P95 too slow: {stats['p95']:.3f}ms"

@pytest.mark.performance
@pytest.mark.stress
class TestStressScenarios:
    """Stress testing scenarios"""
    
    async def test_peak_load_simulation(self, test_config, performance_tracker):
        """Simulate peak load scenarios"""
        
        # Simulate a traffic spike
        phases = [
            {'name': 'ramp_up', 'duration': 30, 'max_concurrent': 25},
            {'name': 'sustained_peak', 'duration': 60, 'max_concurrent': 50},
            {'name': 'ramp_down', 'duration': 30, 'max_concurrent': 10}
        ]
        
        overall_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': []
        }
        
        for phase in phases:
            logger.info(f"Starting stress test phase: {phase['name']}")
            
            phase_start = time.time()
            phase_end = phase_start + phase['duration']
            
            async def stress_worker(worker_id: int):
                """Individual stress test worker"""
                worker_requests = 0
                worker_success = 0
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    while time.time() < phase_end:
                        request_start = time.perf_counter()
                        worker_requests += 1
                        
                        try:
                            # Mix of different endpoints
                            endpoints = ['/health', '/api/v1/health']
                            endpoint = endpoints[worker_requests % len(endpoints)]
                            
                            response = await client.get(f"{test_config['base_url']}{endpoint}")
                            request_time = time.perf_counter() - request_start
                            
                            if response.status_code == 200:
                                worker_success += 1
                                overall_stats['response_times'].append(request_time * 1000)
                            
                        except Exception as e:
                            logger.debug(f"Stress test request failed: {e}")
                        
                        # Adaptive delay based on phase
                        if phase['name'] == 'ramp_up':
                            delay = 0.5 - (time.time() - phase_start) / phase['duration'] * 0.4
                        elif phase['name'] == 'sustained_peak':
                            delay = 0.1  # High frequency
                        else:  # ramp_down
                            delay = 0.1 + (time.time() - phase_start) / phase['duration'] * 0.4
                        
                        await asyncio.sleep(max(0.05, delay))
                
                return {
                    'worker_id': worker_id,
                    'requests': worker_requests,
                    'success': worker_success
                }
            
            # Launch workers
            workers = [stress_worker(i) for i in range(phase['max_concurrent'])]
            worker_results = await asyncio.gather(*workers, return_exceptions=True)
            
            # Aggregate phase results
            phase_requests = sum(r['requests'] for r in worker_results if isinstance(r, dict))
            phase_success = sum(r['success'] for r in worker_results if isinstance(r, dict))
            
            overall_stats['total_requests'] += phase_requests
            overall_stats['successful_requests'] += phase_success
            overall_stats['failed_requests'] += (phase_requests - phase_success)
            
            logger.info(f"Phase {phase['name']} completed - "
                       f"Requests: {phase_requests}, Success: {phase_success}, "
                       f"Success rate: {phase_success/phase_requests:.2%}")
            
            # Brief recovery period between phases
            await asyncio.sleep(5)
        
        # Final analysis
        total_success_rate = overall_stats['successful_requests'] / overall_stats['total_requests']
        avg_response_time = np.mean(overall_stats['response_times'])
        p95_response_time = np.percentile(overall_stats['response_times'], 95)
        
        performance_tracker.add_metric('stress_test_success_rate', total_success_rate)
        performance_tracker.add_metric('stress_test_avg_response_time', avg_response_time)
        performance_tracker.add_metric('stress_test_p95_response_time', p95_response_time)
        
        logger.info("Stress Test Results:")
        logger.info(f"  Total requests: {overall_stats['total_requests']}")
        logger.info(f"  Success rate: {total_success_rate:.2%}")
        logger.info(f"  Average response time: {avg_response_time:.2f}ms")
        logger.info(f"  P95 response time: {p95_response_time:.2f}ms")
        
        # Validate stress test results
        assert total_success_rate >= 0.85, f"Stress test success rate too low: {total_success_rate:.2%}"
        assert avg_response_time < 1000.0, f"Average response time too high under stress: {avg_response_time:.2f}ms"