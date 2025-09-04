"""
Service Communication Integration Tests
Tests for Docker service communication and API connectivity
"""

import pytest
import asyncio
import httpx
import redis
import psycopg2
import time
from typing import Dict, List
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@pytest.mark.integration
class TestServiceCommunication:
    """Test communication between Docker services"""
    
    async def test_postgres_connectivity(self, test_config, performance_tracker):
        """Test PostgreSQL database connectivity and performance"""
        connection_times = []
        
        for i in range(10):  # Test multiple connections
            start_time = time.time()
            try:
                conn = psycopg2.connect(test_config['postgres_url'])
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1, "Database query failed"
                cursor.close()
                conn.close()
                
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
                performance_tracker.add_metric('db_connection_time', connection_time)
                
            except Exception as e:
                pytest.fail(f"Database connection failed: {e}")
        
        # Statistical validation
        avg_connection_time = np.mean(connection_times)
        assert avg_connection_time < 0.1, f"Average connection time too high: {avg_connection_time:.3f}s"
        
        logger.info(f"Database connection stats - Mean: {avg_connection_time:.3f}s, "
                   f"Min: {min(connection_times):.3f}s, Max: {max(connection_times):.3f}s")

    async def test_redis_connectivity(self, test_config, performance_tracker):
        """Test Redis cache connectivity and performance"""
        response_times = []
        
        for i in range(20):  # Test multiple operations
            start_time = time.time()
            try:
                r = redis.from_url(test_config['redis_url'])
                
                # Test basic operations
                test_key = f"test_key_{i}"
                test_value = f"test_value_{i}"
                
                # Set operation
                r.set(test_key, test_value, ex=10)  # 10 second expiry
                
                # Get operation
                retrieved_value = r.get(test_key)
                assert retrieved_value.decode() == test_value, "Redis get/set failed"
                
                # Delete operation
                r.delete(test_key)
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                performance_tracker.add_metric('redis_operation_time', response_time)
                
            except Exception as e:
                pytest.fail(f"Redis operation failed: {e}")
        
        # Statistical validation
        avg_response_time = np.mean(response_times)
        assert avg_response_time < 0.01, f"Average Redis operation time too high: {avg_response_time:.4f}s"
        
        logger.info(f"Redis operation stats - Mean: {avg_response_time:.4f}s, "
                   f"P95: {np.percentile(response_times, 95):.4f}s")

    async def test_api_backend_health(self, test_config, performance_tracker):
        """Test API backend health endpoint"""
        response_times = []
        
        async with httpx.AsyncClient() as client:
            for i in range(15):
                start_time = time.time()
                try:
                    response = await client.get(f"{test_config['base_url']}/health", timeout=10)
                    assert response.status_code == 200, f"Health check failed with status {response.status_code}"
                    
                    response_data = response.json()
                    assert response_data.get('status') == 'healthy', "Service not healthy"
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    performance_tracker.add_metric('api_health_response_time', response_time)
                    
                except Exception as e:
                    pytest.fail(f"API health check failed: {e}")
        
        # Statistical analysis
        avg_response_time = np.mean(response_times)
        p95_response_time = np.percentile(response_times, 95)
        
        assert avg_response_time < 0.5, f"Average health check response time too high: {avg_response_time:.3f}s"
        assert p95_response_time < 1.0, f"P95 health check response time too high: {p95_response_time:.3f}s"
        
        logger.info(f"API health check stats - Mean: {avg_response_time:.3f}s, P95: {p95_response_time:.3f}s")

    async def test_api_documentation_endpoints(self, test_config):
        """Test API documentation availability"""
        async with httpx.AsyncClient() as client:
            # Test Swagger UI
            response = await client.get(f"{test_config['base_url']}/api/docs", timeout=10)
            assert response.status_code == 200, "Swagger UI not accessible"
            
            # Test ReDoc
            response = await client.get(f"{test_config['base_url']}/api/redoc", timeout=10)
            assert response.status_code == 200, "ReDoc not accessible"
            
            # Test OpenAPI schema
            response = await client.get(f"{test_config['base_url']}/openapi.json", timeout=10)
            assert response.status_code == 200, "OpenAPI schema not accessible"
            
            schema = response.json()
            assert 'openapi' in schema, "Invalid OpenAPI schema"
            assert 'paths' in schema, "No API paths in schema"

    async def test_service_dependencies(self, test_config, statistical_validator):
        """Test service dependency chain and response times"""
        dependency_tests = []
        
        # Test API backend -> Database dependency
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            try:
                response = await client.get(f"{test_config['base_url']}/api/v1/health", timeout=10)
                api_response_time = time.time() - start_time
                dependency_tests.append(('api_to_db', api_response_time, response.status_code == 200))
            except Exception as e:
                dependency_tests.append(('api_to_db', float('inf'), False))
        
        # Test API backend -> Redis dependency
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            try:
                # This endpoint should test Redis functionality
                response = await client.get(f"{test_config['base_url']}/api/v1/health", timeout=10)
                redis_response_time = time.time() - start_time
                dependency_tests.append(('api_to_redis', redis_response_time, response.status_code == 200))
            except Exception as e:
                dependency_tests.append(('api_to_redis', float('inf'), False))
        
        # Validate all dependencies are working
        failed_dependencies = [test for test in dependency_tests if not test[2]]
        assert len(failed_dependencies) == 0, f"Failed dependencies: {failed_dependencies}"
        
        # Statistical analysis of response times
        response_times = [test[1] for test in dependency_tests if test[2]]
        if response_times:
            validation_result = statistical_validator.validate_performance(
                response_times, threshold=2.0, test_type='mean'
            )
            assert validation_result['valid'], f"Dependency response times exceed threshold: {validation_result}"

@pytest.mark.integration
@pytest.mark.performance
class TestNetworkPerformance:
    """Test network performance between services"""
    
    async def test_inter_service_latency(self, test_config, performance_tracker):
        """Measure latency between services"""
        latency_measurements = []
        
        # Test multiple endpoints to measure network latency
        endpoints = [
            f"{test_config['base_url']}/health",
            f"{test_config['base_url']}/api/v1/health",
            f"{test_config['base_url']}/"
        ]
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                endpoint_latencies = []
                
                for i in range(10):  # 10 measurements per endpoint
                    start_time = time.time()
                    try:
                        response = await client.get(endpoint, timeout=5)
                        latency = time.time() - start_time
                        
                        if response.status_code == 200:
                            endpoint_latencies.append(latency)
                            performance_tracker.add_metric('network_latency', latency)
                    
                    except Exception as e:
                        logger.warning(f"Network latency test failed for {endpoint}: {e}")
                
                if endpoint_latencies:
                    latency_measurements.extend(endpoint_latencies)
                    avg_latency = np.mean(endpoint_latencies)
                    logger.info(f"Endpoint {endpoint} - Avg latency: {avg_latency:.3f}s")
        
        # Statistical validation
        if latency_measurements:
            overall_avg_latency = np.mean(latency_measurements)
            p95_latency = np.percentile(latency_measurements, 95)
            
            assert overall_avg_latency < 0.5, f"Average network latency too high: {overall_avg_latency:.3f}s"
            assert p95_latency < 1.0, f"P95 network latency too high: {p95_latency:.3f}s"
            
            logger.info(f"Overall network performance - Mean: {overall_avg_latency:.3f}s, "
                       f"P95: {p95_latency:.3f}s, Samples: {len(latency_measurements)}")

    async def test_concurrent_connections(self, test_config, performance_tracker):
        """Test concurrent connection handling"""
        concurrent_levels = [5, 10, 20]  # Different concurrency levels
        
        for concurrency in concurrent_levels:
            logger.info(f"Testing {concurrency} concurrent connections")
            
            async def make_request(session: httpx.AsyncClient, request_id: int):
                start_time = time.time()
                try:
                    response = await session.get(f"{test_config['base_url']}/health", timeout=10)
                    response_time = time.time() - start_time
                    return {
                        'request_id': request_id,
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    }
                except Exception as e:
                    return {
                        'request_id': request_id,
                        'response_time': time.time() - start_time,
                        'status_code': None,
                        'success': False,
                        'error': str(e)
                    }
            
            async with httpx.AsyncClient() as client:
                tasks = [make_request(client, i) for i in range(concurrency)]
                results = await asyncio.gather(*tasks)
            
            # Analyze results
            successful_requests = [r for r in results if r['success']]
            failed_requests = [r for r in results if not r['success']]
            
            success_rate = len(successful_requests) / len(results)
            assert success_rate >= 0.95, f"Success rate too low at concurrency {concurrency}: {success_rate:.2%}"
            
            if successful_requests:
                response_times = [r['response_time'] for r in successful_requests]
                avg_response_time = np.mean(response_times)
                performance_tracker.add_metric('concurrent_response_time', avg_response_time)
                
                logger.info(f"Concurrency {concurrency} - Success rate: {success_rate:.2%}, "
                           f"Avg response time: {avg_response_time:.3f}s")
            
            # Brief pause between concurrency tests
            await asyncio.sleep(1)

    async def test_connection_pooling(self, test_config, performance_tracker):
        """Test connection pooling efficiency"""
        # Test with connection reuse vs new connections
        
        # Test 1: Sequential requests with connection reuse
        reuse_times = []
        async with httpx.AsyncClient() as client:
            for i in range(20):
                start_time = time.time()
                response = await client.get(f"{test_config['base_url']}/health")
                response_time = time.time() - start_time
                if response.status_code == 200:
                    reuse_times.append(response_time)
        
        # Test 2: Sequential requests with new connections each time
        new_connection_times = []
        for i in range(20):
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{test_config['base_url']}/health")
                response_time = time.time() - start_time
                if response.status_code == 200:
                    new_connection_times.append(response_time)
        
        # Compare performance
        if reuse_times and new_connection_times:
            avg_reuse_time = np.mean(reuse_times)
            avg_new_connection_time = np.mean(new_connection_times)
            
            improvement_ratio = avg_new_connection_time / avg_reuse_time
            
            logger.info(f"Connection reuse improvement: {improvement_ratio:.2f}x faster")
            logger.info(f"Reused connections avg: {avg_reuse_time:.3f}s")
            logger.info(f"New connections avg: {avg_new_connection_time:.3f}s")
            
            # Connection reuse should be at least 10% faster
            assert improvement_ratio > 1.1, f"Connection pooling not effective: {improvement_ratio:.2f}x"
            
            performance_tracker.add_metric('connection_reuse_ratio', improvement_ratio)