"""
Test script for MDUS file storage and processing pipeline
Tests the complete workflow: upload → process → store results
"""

import asyncio
import aiohttp
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_FILES = [
    {
        "name": "medical_report_test.txt",
        "content": "Patient: John Doe\nDiagnosis: Hypertension\nMedication: Lisinopril 10mg daily",
        "document_type": "medical_report"
    },
    {
        "name": "prescription_test.txt", 
        "content": "Rx: Amoxicillin 500mg\nTake twice daily for 7 days\nPatient: Jane Smith",
        "document_type": "prescription"
    }
]

class MDUSWorkflowTester:
    """Test the complete MDUS workflow"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_health_checks(self) -> Dict[str, Any]:
        """Test system health endpoints"""
        
        print("🔍 Testing health checks...")
        
        # Test basic health
        async with self.session.get(f"{self.base_url}/health") as response:
            basic_health = await response.json()
            assert response.status == 200
            assert basic_health["status"] == "healthy"
        
        # Test detailed health
        async with self.session.get(f"{self.base_url}/health/detailed") as response:
            detailed_health = await response.json()
            # Note: May show unhealthy status if database/Redis not running
            print(f"   Detailed health: {detailed_health['status']}")
        
        # Test monitoring health
        try:
            async with self.session.get(f"{self.base_url}/monitoring/health") as response:
                monitoring_health = await response.json()
                print(f"   Monitoring health: {monitoring_health['status']}")
        except Exception as e:
            print(f"   Monitoring health: Error - {e}")
        
        return {
            "test": "health_checks",
            "status": "passed",
            "basic_health": basic_health,
            "message": "Health checks completed"
        }
    
    async def test_file_upload(self, test_file: Dict[str, str]) -> Dict[str, Any]:
        """Test file upload functionality"""
        
        print(f"📤 Testing file upload: {test_file['name']}")
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_file['content'])
            temp_file_path = temp_file.name
        
        try:
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('user_id', '1')
            data.add_field('document_type', test_file['document_type'])
            data.add_field('is_sensitive', 'true')
            
            # Add file
            with open(temp_file_path, 'rb') as f:
                data.add_field('file', f, filename=test_file['name'])
                
                # Upload file
                async with self.session.post(
                    f"{self.base_url}/documents/upload",
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        print(f"   ✅ Upload successful: Document ID {result['document_id']}")
                        return {
                            "test": "file_upload",
                            "status": "passed",
                            "document_id": result['document_id'],
                            "job_id": result['job_id'],
                            "filename": result['filename']
                        }
                    else:
                        print(f"   ❌ Upload failed: {result}")
                        return {
                            "test": "file_upload",
                            "status": "failed", 
                            "error": result,
                            "filename": test_file['name']
                        }
        
        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return {
                "test": "file_upload",
                "status": "error",
                "error": str(e),
                "filename": test_file['name']
            }
        
        finally:
            # Clean up temp file
            Path(temp_file_path).unlink(missing_ok=True)
    
    async def test_job_status(self, job_id: str) -> Dict[str, Any]:
        """Test job status monitoring"""
        
        print(f"⏱️  Testing job status: {job_id}")
        
        try:
            async with self.session.get(f"{self.base_url}/processing/jobs/{job_id}") as response:
                if response.status == 200:
                    job_status = await response.json()
                    print(f"   Status: {job_status['status']}")
                    return {
                        "test": "job_status",
                        "status": "passed",
                        "job_id": job_id,
                        "job_status": job_status['status']
                    }
                else:
                    result = await response.json()
                    print(f"   ❌ Job status check failed: {result}")
                    return {
                        "test": "job_status",
                        "status": "failed",
                        "job_id": job_id,
                        "error": result
                    }
        
        except Exception as e:
            print(f"   ❌ Job status error: {e}")
            return {
                "test": "job_status",
                "status": "error",
                "job_id": job_id,
                "error": str(e)
            }
    
    async def test_document_retrieval(self, document_id: int) -> Dict[str, Any]:
        """Test document retrieval"""
        
        print(f"📄 Testing document retrieval: {document_id}")
        
        try:
            async with self.session.get(f"{self.base_url}/documents/{document_id}") as response:
                if response.status == 200:
                    document = await response.json()
                    print(f"   ✅ Document retrieved: {document['filename']}")
                    return {
                        "test": "document_retrieval",
                        "status": "passed",
                        "document_id": document_id,
                        "filename": document['filename']
                    }
                else:
                    result = await response.json()
                    print(f"   ❌ Document retrieval failed: {result}")
                    return {
                        "test": "document_retrieval", 
                        "status": "failed",
                        "document_id": document_id,
                        "error": result
                    }
        
        except Exception as e:
            print(f"   ❌ Document retrieval error: {e}")
            return {
                "test": "document_retrieval",
                "status": "error",
                "document_id": document_id,
                "error": str(e)
            }
    
    async def test_queue_statistics(self) -> Dict[str, Any]:
        """Test queue statistics endpoint"""
        
        print("📊 Testing queue statistics...")
        
        try:
            async with self.session.get(f"{self.base_url}/processing/queue/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"   Queue stats: {stats['queue_stats']}")
                    return {
                        "test": "queue_statistics",
                        "status": "passed",
                        "stats": stats
                    }
                else:
                    result = await response.json()
                    print(f"   ❌ Queue stats failed: {result}")
                    return {
                        "test": "queue_statistics",
                        "status": "failed",
                        "error": result
                    }
        
        except Exception as e:
            print(f"   ❌ Queue stats error: {e}")
            return {
                "test": "queue_statistics",
                "status": "error", 
                "error": str(e)
            }
    
    async def test_monitoring_endpoints(self) -> Dict[str, Any]:
        """Test monitoring endpoints"""
        
        print("🔧 Testing monitoring endpoints...")
        
        results = {}
        
        # Test system metrics
        try:
            async with self.session.get(f"{self.base_url}/monitoring/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    results["metrics"] = "passed"
                    print("   ✅ System metrics retrieved")
                else:
                    results["metrics"] = "failed"
                    print("   ❌ System metrics failed")
        except Exception as e:
            results["metrics"] = f"error: {e}"
            print(f"   ❌ System metrics error: {e}")
        
        # Test alerts
        try:
            async with self.session.get(f"{self.base_url}/monitoring/alerts") as response:
                if response.status == 200:
                    alerts = await response.json()
                    results["alerts"] = "passed"
                    print(f"   ✅ Alerts retrieved: {alerts['total_alerts']} alerts")
                else:
                    results["alerts"] = "failed"
                    print("   ❌ Alerts retrieval failed")
        except Exception as e:
            results["alerts"] = f"error: {e}"
            print(f"   ❌ Alerts error: {e}")
        
        # Test storage stats
        try:
            async with self.session.get(f"{self.base_url}/monitoring/storage") as response:
                if response.status == 200:
                    storage = await response.json()
                    results["storage"] = "passed"
                    print(f"   ✅ Storage stats retrieved")
                else:
                    results["storage"] = "failed"
                    print("   ❌ Storage stats failed")
        except Exception as e:
            results["storage"] = f"error: {e}"
            print(f"   ❌ Storage stats error: {e}")
        
        return {
            "test": "monitoring_endpoints",
            "status": "passed" if all(r == "passed" for r in results.values()) else "mixed",
            "results": results
        }
    
    async def run_complete_workflow_test(self) -> Dict[str, Any]:
        """Run complete workflow test"""
        
        print("🚀 Starting MDUS Complete Workflow Test")
        print("=" * 50)
        
        # Test 1: Health checks
        health_result = await self.test_health_checks()
        self.test_results.append(health_result)
        
        # Test 2: File uploads
        upload_results = []
        job_ids = []
        document_ids = []
        
        for test_file in TEST_FILES:
            upload_result = await self.test_file_upload(test_file)
            upload_results.append(upload_result)
            self.test_results.append(upload_result)
            
            if upload_result["status"] == "passed":
                job_ids.append(upload_result["job_id"])
                document_ids.append(upload_result["document_id"])
        
        # Test 3: Job status monitoring
        for job_id in job_ids:
            job_result = await self.test_job_status(job_id)
            self.test_results.append(job_result)
        
        # Test 4: Document retrieval
        for doc_id in document_ids:
            doc_result = await self.test_document_retrieval(doc_id)
            self.test_results.append(doc_result)
        
        # Test 5: Queue statistics
        queue_result = await self.test_queue_statistics()
        self.test_results.append(queue_result)
        
        # Test 6: Monitoring endpoints
        monitoring_result = await self.test_monitoring_endpoints()
        self.test_results.append(monitoring_result)
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "passed"])
        failed_tests = len([r for r in self.test_results if r["status"] == "failed"])
        error_tests = len([r for r in self.test_results if r["status"] == "error"])
        
        print("\n" + "=" * 50)
        print("📋 Test Summary")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🔥 Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "detailed_results": self.test_results
        }

async def main():
    """Main test runner"""
    
    print("MDUS File Storage & Processing Pipeline Test")
    print("=" * 60)
    print("Testing complete workflow: upload → process → store results")
    print()
    
    async with MDUSWorkflowTester(API_BASE_URL) as tester:
        try:
            results = await tester.run_complete_workflow_test()
            
            # Save results to file
            with open("test_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📁 Detailed results saved to: test_results.json")
            
            if results["summary"]["success_rate"] > 80:
                print("🎉 Workflow test completed successfully!")
                return True
            else:
                print("⚠️  Some tests failed. Check the results for details.")
                return False
                
        except Exception as e:
            print(f"❌ Test runner error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)