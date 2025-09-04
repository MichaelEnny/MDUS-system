"""
MDUS Integration Testing Configuration
Pytest configuration for comprehensive integration testing with statistical analysis
"""

import os
import asyncio
import pytest
import docker
import psutil
import logging
from typing import Dict, Any, AsyncGenerator
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Test configuration
TEST_CONFIG = {
    'base_url': 'http://localhost:8000',
    'ai_service_url': 'http://localhost:8001', 
    'frontend_url': 'http://localhost:3000',
    'postgres_url': 'postgresql://mdus_user:mdus_password@localhost:5432/mdus_db',
    'redis_url': 'redis://:redis_password@localhost:6379/0',
    'test_timeout': 300,  # 5 minutes
    'performance_samples': 50,  # Number of samples for statistical analysis
    'confidence_level': 0.95,  # 95% confidence intervals
    'random_seed': 42,  # For reproducible results
}

# Set random seeds for reproducibility
np.random.seed(TEST_CONFIG['random_seed'])

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return TEST_CONFIG

@pytest.fixture(scope="session")
async def docker_services():
    """Ensure Docker services are running and healthy"""
    client = docker.from_env()
    services = ['mdus_postgres', 'mdus_redis', 'mdus_api_backend']
    
    # Check if services are running
    running_containers = {c.name: c for c in client.containers.list() if c.name in services}
    
    # Wait for services to be healthy
    for service_name in services:
        if service_name in running_containers:
            container = running_containers[service_name]
            # Wait for health check to pass
            for _ in range(30):  # 30 second timeout
                container.reload()
                if container.attrs.get('State', {}).get('Health', {}).get('Status') == 'healthy':
                    break
                await asyncio.sleep(1)
    
    yield running_containers
    
    # Cleanup is handled by docker-compose

@pytest.fixture(scope="session")
def performance_tracker():
    """Track performance metrics across tests"""
    metrics = {
        'response_times': [],
        'memory_usage': [],
        'cpu_usage': [],
        'error_rates': [],
        'throughput': []
    }
    
    def add_metric(metric_type: str, value: float):
        if metric_type in metrics:
            metrics[metric_type].append(value)
    
    def get_statistics(metric_type: str) -> Dict[str, float]:
        """Calculate statistical summary for a metric"""
        if metric_type not in metrics or not metrics[metric_type]:
            return {}
        
        data = np.array(metrics[metric_type])
        return {
            'mean': np.mean(data),
            'median': np.median(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'p95': np.percentile(data, 95),
            'p99': np.percentile(data, 99),
            'count': len(data)
        }
    
    def generate_report() -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'config': TEST_CONFIG,
            'metrics': {}
        }
        
        for metric_type in metrics:
            report['metrics'][metric_type] = get_statistics(metric_type)
        
        return report
    
    tracker = type('PerformanceTracker', (), {
        'add_metric': add_metric,
        'get_statistics': get_statistics,
        'generate_report': generate_report,
        'metrics': metrics
    })()
    
    yield tracker

@pytest.fixture(scope="function")
def system_monitor():
    """Monitor system resources during test execution"""
    initial_stats = {
        'memory': psutil.virtual_memory(),
        'cpu': psutil.cpu_percent(interval=1),
        'disk': psutil.disk_usage('/'),
        'network': psutil.net_io_counters()
    }
    
    def get_current_stats():
        return {
            'memory': psutil.virtual_memory(),
            'cpu': psutil.cpu_percent(),
            'disk': psutil.disk_usage('/'),
            'network': psutil.net_io_counters()
        }
    
    def calculate_usage_diff(start_stats, end_stats):
        """Calculate resource usage difference"""
        return {
            'memory_diff': end_stats['memory'].used - start_stats['memory'].used,
            'cpu_avg': end_stats['cpu'],
            'network_sent_diff': end_stats['network'].bytes_sent - start_stats['network'].bytes_sent,
            'network_recv_diff': end_stats['network'].bytes_recv - start_stats['network'].bytes_recv
        }
    
    monitor = type('SystemMonitor', (), {
        'initial_stats': initial_stats,
        'get_current_stats': get_current_stats,
        'calculate_usage_diff': calculate_usage_diff
    })()
    
    yield monitor

@pytest.fixture(scope="function")
def statistical_validator():
    """Statistical validation utilities"""
    from scipy import stats
    
    def validate_performance(samples: list, threshold: float, test_type: str = 'mean') -> Dict[str, Any]:
        """Validate performance against threshold with statistical significance"""
        if not samples:
            return {'valid': False, 'reason': 'No samples provided'}
        
        data = np.array(samples)
        
        if test_type == 'mean':
            statistic, p_value = stats.ttest_1samp(data, threshold)
            result = {
                'valid': np.mean(data) <= threshold,
                'mean': np.mean(data),
                'threshold': threshold,
                'p_value': p_value,
                'statistic': statistic,
                'test_type': 'one_sample_ttest'
            }
        elif test_type == 'percentile':
            p95 = np.percentile(data, 95)
            result = {
                'valid': p95 <= threshold,
                'p95': p95,
                'threshold': threshold,
                'test_type': 'percentile_95'
            }
        
        # Add confidence interval
        confidence_level = TEST_CONFIG['confidence_level']
        margin_error = stats.norm.ppf((1 + confidence_level) / 2) * stats.sem(data)
        result['confidence_interval'] = {
            'lower': np.mean(data) - margin_error,
            'upper': np.mean(data) + margin_error,
            'level': confidence_level
        }
        
        return result
    
    def compare_distributions(sample1: list, sample2: list) -> Dict[str, Any]:
        """Compare two performance distributions"""
        if not sample1 or not sample2:
            return {'valid': False, 'reason': 'Insufficient samples'}
        
        # Kolmogorov-Smirnov test for distribution comparison
        ks_stat, ks_p = stats.ks_2samp(sample1, sample2)
        
        # Mann-Whitney U test for median comparison
        mw_stat, mw_p = stats.mannwhitneyu(sample1, sample2, alternative='two-sided')
        
        return {
            'ks_test': {'statistic': ks_stat, 'p_value': ks_p},
            'mann_whitney': {'statistic': mw_stat, 'p_value': mw_p},
            'sample1_stats': {
                'mean': np.mean(sample1),
                'median': np.median(sample1),
                'std': np.std(sample1)
            },
            'sample2_stats': {
                'mean': np.mean(sample2),
                'median': np.median(sample2),
                'std': np.std(sample2)
            }
        }
    
    validator = type('StatisticalValidator', (), {
        'validate_performance': validate_performance,
        'compare_distributions': compare_distributions
    })()
    
    yield validator

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_tests.log'),
        logging.StreamHandler()
    ]
)

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "stress: Stress tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

def pytest_html_report_title(report):
    """Customize HTML report title"""
    report.title = "MDUS Integration Test Report"

def pytest_sessionfinish(session, exitstatus):
    """Generate final test report"""
    # This will be called after all tests complete
    print(f"Integration test session finished with exit status: {exitstatus}")