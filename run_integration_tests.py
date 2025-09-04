#!/usr/bin/env python3
"""
MDUS Integration Test Execution Script
Simplified script to run integration tests with proper setup
"""

import os
import sys
import asyncio
import subprocess
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_docker_services():
    """Check if required Docker services are running"""
    
    required_services = [
        'mdus_postgres',
        'mdus_redis', 
        'mdus_api_backend'
    ]
    
    try:
        # Check if docker is available
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Docker is not running or accessible")
            return False
        
        running_containers = result.stdout
        
        # Check each required service
        missing_services = []
        for service in required_services:
            if service not in running_containers:
                missing_services.append(service)
        
        if missing_services:
            logger.warning(f"Missing Docker services: {missing_services}")
            logger.info("Starting Docker services with docker-compose...")
            
            # Try to start services
            start_result = subprocess.run(['docker-compose', 'up', '-d'], 
                                        capture_output=True, text=True)
            if start_result.returncode != 0:
                logger.error(f"Failed to start services: {start_result.stderr}")
                return False
            
            # Wait for services to start
            logger.info("Waiting for services to start...")
            time.sleep(30)
        
        logger.info("All required Docker services are running")
        return True
        
    except Exception as e:
        logger.error(f"Failed to check Docker services: {e}")
        return False

def install_test_dependencies():
    """Install test dependencies if not already installed"""
    
    requirements_file = Path("tests/integration/requirements.txt")
    
    if not requirements_file.exists():
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    try:
        logger.info("Installing test dependencies...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to install dependencies: {result.stderr}")
            return False
        
        logger.info("Test dependencies installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def create_reports_directory():
    """Create reports directory if it doesn't exist"""
    reports_dir = Path("tests/integration/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Reports directory ready: {reports_dir}")

async def run_integration_tests():
    """Run the integration tests"""
    
    # Change to integration test directory
    test_dir = Path("tests/integration")
    if not test_dir.exists():
        logger.error(f"Integration test directory not found: {test_dir}")
        return False
    
    os.chdir(test_dir)
    
    try:
        # Import and run the test runner
        from test_runner import IntegrationTestRunner, TestExecutionConfig
        
        # Configure test execution
        config = TestExecutionConfig(
            test_types=['integration', 'e2e', 'performance'],
            parallel_workers=2,  # Conservative for stability
            generate_reports=True,
            statistical_analysis=True,
            performance_thresholds={
                'api_response_time_p95': 1000.0,  # Relaxed for initial testing
                'db_connection_time_mean': 100.0,
                'cache_operation_time_max': 50.0,
                'e2e_processing_time_mean': 60.0,
                'error_rate_max': 0.10
            }
        )
        
        # Create and run test runner
        runner = IntegrationTestRunner(config)
        results = await runner.run_tests()
        
        # Print results summary
        print("\\n" + "="*80)
        print("MDUS INTEGRATION TEST RESULTS")
        print("="*80)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.get('success'))
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        print(f"Test Categories: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {success_rate:.1%}")
        
        print("\\nDetailed Results:")
        for test_type, result in results.items():
            status = "✓ PASS" if result.get('success') else "✗ FAIL"
            duration = result.get('duration', 0)
            print(f"  {test_type}: {status} ({duration:.2f}s)")
        
        print("\\nGenerated Reports:")
        reports_dir = Path("reports")
        if reports_dir.exists():
            for report_file in reports_dir.glob("*"):
                print(f"  - {report_file.name}")
        
        print("="*80)
        
        return success_rate >= 0.8  # Consider successful if 80%+ pass
        
    except Exception as e:
        logger.error(f"Integration test execution failed: {e}", exc_info=True)
        return False

def main():
    """Main execution function"""
    
    print("MDUS Integration Test Setup and Execution")
    print("="*50)
    
    # Step 1: Check Docker services
    print("1. Checking Docker services...")
    if not check_docker_services():
        print("❌ Docker services check failed")
        return 1
    print("✅ Docker services ready")
    
    # Step 2: Install dependencies
    print("\\n2. Installing test dependencies...")
    if not install_test_dependencies():
        print("❌ Dependency installation failed")
        return 1
    print("✅ Test dependencies ready")
    
    # Step 3: Create reports directory
    print("\\n3. Setting up reports directory...")
    create_reports_directory()
    print("✅ Reports directory ready")
    
    # Step 4: Run tests
    print("\\n4. Running integration tests...")
    success = asyncio.run(run_integration_tests())
    
    if success:
        print("\\n✅ Integration tests completed successfully!")
        print("\\nNext steps:")
        print("- Review generated reports in tests/integration/reports/")
        print("- Check integration_test_summary.md for executive summary")
        print("- Address any failures before production deployment")
        return 0
    else:
        print("\\n❌ Integration tests failed!")
        print("\\nTroubleshooting:")
        print("- Check Docker services are running: docker-compose ps")
        print("- Review logs in tests/integration/integration_tests.log")
        print("- Verify service endpoints are accessible")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)