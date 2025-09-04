# MDUS Integration Testing Framework

A comprehensive integration testing framework for the Multi-Document Understanding System (MDUS) with statistical analysis and performance benchmarking.

## Overview

This testing framework provides:
- **Service Communication Testing**: Validates Docker service connectivity and API endpoints
- **End-to-End Workflow Testing**: Tests complete document processing pipelines
- **Performance Benchmarking**: Statistical analysis of system performance
- **Error Scenario Testing**: Comprehensive error handling validation
- **Statistical Validation**: Rigorous statistical analysis of performance metrics

## Features

### Statistical Analysis
- Confidence intervals for performance metrics
- Hypothesis testing for performance thresholds
- Distribution analysis and normality testing
- Outlier detection and variance analysis
- Reproducible results with proper seed management

### Performance Testing
- Response time distribution analysis
- Throughput testing under various load levels
- Resource utilization monitoring (CPU, memory)
- Database and cache performance validation
- Network latency measurements

### Test Document Generation
- Varied document types (text, forms, tables)
- Different sizes and quality variations
- Medical document templates
- Metadata-rich test cases

## Setup

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- MDUS system running locally

### Installation

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure MDUS services are running:
```bash
docker-compose up -d
```

3. Verify service availability:
```bash
curl http://localhost:8000/health
curl http://localhost:3000
```

## Usage

### Quick Start
Run all integration tests:
```bash
python test_runner.py
```

### Running Specific Test Categories

```bash
# Integration tests only
pytest -m integration

# End-to-end tests only
pytest -m e2e

# Performance tests only
pytest -m performance

# Stress tests only
pytest -m stress
```

### Custom Test Execution

```python
from test_runner import IntegrationTestRunner, TestExecutionConfig

config = TestExecutionConfig(
    test_types=['integration', 'performance'],
    parallel_workers=4,
    generate_reports=True,
    performance_thresholds={
        'api_response_time_p95': 500.0,  # 500ms
        'error_rate_max': 0.05  # 5%
    }
)

runner = IntegrationTestRunner(config)
results = await runner.run_tests()
```

## Test Structure

### Test Categories

1. **Service Communication Tests** (`test_service_communication.py`)
   - PostgreSQL connectivity and performance
   - Redis cache operations
   - API endpoint availability
   - Network performance between services

2. **End-to-End Workflow Tests** (`test_e2e_workflow.py`)
   - Document upload and processing pipeline
   - Batch document processing
   - Document retrieval workflows
   - Concurrent processing scenarios
   - Error handling in workflows

3. **Performance Benchmark Tests** (`test_performance_benchmarks.py`)
   - API response time distribution analysis
   - Throughput under load testing
   - System resource usage monitoring
   - Database and cache performance
   - Stress testing scenarios

### Test Fixtures

- **test_config**: Basic test configuration
- **docker_services**: Docker service management
- **performance_tracker**: Performance metric collection
- **system_monitor**: System resource monitoring
- **statistical_validator**: Statistical validation utilities

## Statistical Methodology

### Performance Validation
- **Confidence Level**: 95% (configurable)
- **Sample Size**: Minimum 50 samples for statistical significance
- **Threshold Testing**: One-sample t-tests against performance thresholds
- **Distribution Analysis**: Kolmogorov-Smirnov and Shapiro-Wilk tests

### Metrics Collected
- Response times (mean, median, P95, P99)
- Error rates and success rates
- Resource utilization (CPU, memory)
- Database query performance
- Cache operation times
- Network latency

## Reports Generated

### 1. Performance Analysis Report
- Comprehensive performance metrics
- Statistical summaries with confidence intervals
- Threshold compliance analysis
- Resource utilization trends

### 2. Statistical Analysis Report
- Normality test results
- Hypothesis test outcomes
- Effect size calculations
- Confidence interval analysis

### 3. Executive Summary Report
- High-level test results
- System readiness assessment
- Key recommendations
- Next steps for deployment

### 4. Test Documentation
- Generated test documents metadata
- Document type distribution
- Processing complexity analysis

## Configuration

### Performance Thresholds
```python
performance_thresholds = {
    'api_response_time_p95': 500.0,     # 500ms P95 response time
    'db_connection_time_mean': 50.0,    # 50ms mean connection time
    'cache_operation_time_max': 10.0,   # 10ms max cache operation
    'e2e_processing_time_mean': 30.0,   # 30s mean E2E processing
    'error_rate_max': 0.05              # 5% maximum error rate
}
```

### Test Execution Configuration
```python
config = TestExecutionConfig(
    test_types=['integration', 'e2e', 'performance'],
    parallel_workers=4,
    timeout_seconds=3600,
    generate_reports=True,
    statistical_analysis=True,
    performance_thresholds=performance_thresholds
)
```

## Sample Test Documents

The framework generates various test documents:

### Document Types
- **Text Documents**: Simple text content with medical information
- **Form Documents**: Structured forms with fields and values
- **Table Documents**: Tabular data like lab results and medication lists
- **Variation Documents**: Different sizes and orientations
- **Quality Test Documents**: Various visual characteristics for OCR testing

### Document Statistics
- Total documents generated: 15-20
- Size range: 300x200 to 1200x800 pixels
- Complexity levels: Low, Medium, High
- Format variations: Portrait, landscape, square

## Best Practices

### Test Development
1. Use appropriate statistical sample sizes (≥50 for performance tests)
2. Set random seeds for reproducible results
3. Include proper error handling and timeout management
4. Validate assumptions with statistical tests

### Performance Testing
1. Warm up systems before measurement
2. Use confidence intervals for performance claims
3. Test multiple load levels and scenarios
4. Monitor system resources during tests

### Error Handling
1. Test both expected and unexpected error scenarios
2. Validate error response formats and codes
3. Ensure graceful degradation under stress
4. Test recovery mechanisms

## Troubleshooting

### Common Issues

1. **Service Connection Failures**
   - Verify Docker services are running
   - Check port configurations
   - Validate environment variables

2. **Test Timeouts**
   - Increase timeout values in configuration
   - Check system resource availability
   - Verify network connectivity

3. **Statistical Validation Failures**
   - Review sample sizes (minimum 30-50)
   - Check for outliers in data
   - Validate performance thresholds

### Debug Mode
Enable debug logging:
```bash
pytest --log-cli-level=DEBUG
```

## Contributing

When adding new tests:

1. Follow existing test patterns and naming conventions
2. Include appropriate statistical validation
3. Add performance tracking where relevant
4. Update documentation and markers
5. Ensure tests are idempotent and can run in parallel

## Output Files

After test execution:

```
reports/
├── integration_test_report.html     # Pytest HTML report
├── performance_analysis.json        # Performance metrics
├── statistical_analysis.json        # Statistical analysis
├── executive_summary.json          # Executive summary
├── integration_test_summary.md     # Readable summary
└── raw_test_data.json              # Raw execution data

test_documents/
├── document_metadata.json          # Test document metadata
├── text_document_*.png             # Generated text documents
├── form_document_*.png             # Generated form documents
└── table_document_*.png            # Generated table documents

logs/
├── integration_tests.log           # Test execution log
└── integration_test_execution.log  # Runner execution log
```

---

**Note**: This framework is designed for comprehensive integration testing with statistical rigor. For unit tests, use the standard pytest framework in the respective service directories.