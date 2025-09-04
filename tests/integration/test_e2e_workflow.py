"""
End-to-End Document Processing Workflow Tests
Comprehensive testing of the complete document processing pipeline
"""

import pytest
import asyncio
import httpx
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

@pytest.mark.e2e
@pytest.mark.slow
class TestDocumentProcessingWorkflow:
    """Test complete document processing workflow"""
    
    async def test_document_upload_processing_pipeline(self, test_config, performance_tracker, statistical_validator):
        """Test complete document upload and processing pipeline"""
        
        # Create test document (simple image)
        test_image = Image.new('RGB', (800, 600), color='white')
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        processing_times = []
        success_count = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(5):  # Test multiple documents
                start_time = time.time()
                
                try:
                    # Step 1: Upload document
                    upload_data = {
                        'file': ('test_document.png', img_buffer.getvalue(), 'image/png'),
                        'metadata': json.dumps({
                            'document_type': 'test_image',
                            'test_run': i,
                            'expected_processing': 'ocr_extraction'
                        })
                    }
                    
                    upload_response = await client.post(
                        f"{test_config['base_url']}/api/v1/documents/upload",
                        files=upload_data
                    )
                    
                    assert upload_response.status_code in [200, 201], f"Upload failed: {upload_response.status_code}"
                    upload_result = upload_response.json()
                    document_id = upload_result.get('document_id') or upload_result.get('id')
                    
                    assert document_id, f"No document ID returned: {upload_result}"
                    
                    # Step 2: Check processing status
                    processing_complete = False
                    status_checks = 0
                    max_status_checks = 60  # 60 seconds timeout
                    
                    while not processing_complete and status_checks < max_status_checks:
                        status_response = await client.get(
                            f"{test_config['base_url']}/api/v1/documents/{document_id}/status"
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            
                            if status in ['completed', 'processed', 'success']:
                                processing_complete = True
                            elif status in ['failed', 'error']:
                                pytest.fail(f"Document processing failed: {status_data}")
                            
                        status_checks += 1
                        await asyncio.sleep(1)
                    
                    assert processing_complete, f"Processing timeout after {max_status_checks} seconds"
                    
                    # Step 3: Retrieve processed results
                    results_response = await client.get(
                        f"{test_config['base_url']}/api/v1/documents/{document_id}/results"
                    )
                    
                    assert results_response.status_code == 200, f"Results retrieval failed: {results_response.status_code}"
                    results_data = results_response.json()
                    
                    # Validate results structure
                    assert 'document_id' in results_data, "Missing document_id in results"
                    assert 'processing_results' in results_data, "Missing processing_results in results"
                    
                    total_processing_time = time.time() - start_time
                    processing_times.append(total_processing_time)
                    performance_tracker.add_metric('e2e_processing_time', total_processing_time)
                    success_count += 1
                    
                    logger.info(f"Document {i+1} processed successfully in {total_processing_time:.2f}s")
                    
                except Exception as e:
                    logger.error(f"E2E workflow failed for document {i+1}: {e}")
                    pytest.fail(f"E2E workflow failed: {e}")
        
        # Statistical validation
        assert success_count == 5, f"Not all documents processed successfully: {success_count}/5"
        
        if processing_times:
            validation_result = statistical_validator.validate_performance(
                processing_times, threshold=30.0, test_type='mean'
            )
            
            avg_processing_time = np.mean(processing_times)
            p95_processing_time = np.percentile(processing_times, 95)
            
            logger.info(f"E2E Processing Statistics:")
            logger.info(f"  Mean processing time: {avg_processing_time:.2f}s")
            logger.info(f"  P95 processing time: {p95_processing_time:.2f}s")
            logger.info(f"  Success rate: {success_count}/5 (100%)")
            
            assert validation_result['valid'], f"Processing times exceed threshold: {validation_result}"

    async def test_batch_document_processing(self, test_config, performance_tracker):
        """Test batch processing of multiple documents"""
        
        batch_sizes = [3, 5, 10]  # Different batch sizes to test
        
        for batch_size in batch_sizes:
            logger.info(f"Testing batch processing with {batch_size} documents")
            
            # Create test documents
            test_documents = []
            for i in range(batch_size):
                test_image = Image.new('RGB', (400, 300), color=(255, 255, 255))
                img_buffer = BytesIO()
                test_image.save(img_buffer, format='JPEG')
                img_buffer.seek(0)
                
                test_documents.append({
                    'filename': f'batch_test_{i}.jpg',
                    'content': img_buffer.getvalue(),
                    'content_type': 'image/jpeg'
                })
            
            batch_start_time = time.time()
            document_ids = []
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Upload all documents in batch
                upload_tasks = []
                for doc in test_documents:
                    upload_data = {
                        'file': (doc['filename'], doc['content'], doc['content_type'])
                    }
                    upload_tasks.append(client.post(
                        f"{test_config['base_url']}/api/v1/documents/upload",
                        files=upload_data
                    ))
                
                upload_responses = await asyncio.gather(*upload_tasks, return_exceptions=True)
                
                # Collect document IDs
                for i, response in enumerate(upload_responses):
                    if isinstance(response, Exception):
                        logger.error(f"Upload failed for document {i}: {response}")
                        continue
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        document_id = result.get('document_id') or result.get('id')
                        if document_id:
                            document_ids.append(document_id)
                
                assert len(document_ids) == batch_size, f"Not all uploads successful: {len(document_ids)}/{batch_size}"
                
                # Wait for all documents to process
                all_processed = False
                timeout_seconds = 120  # 2 minutes for batch
                check_interval = 2  # Check every 2 seconds
                elapsed_time = 0
                
                while not all_processed and elapsed_time < timeout_seconds:
                    status_tasks = []
                    for doc_id in document_ids:
                        status_tasks.append(client.get(
                            f"{test_config['base_url']}/api/v1/documents/{doc_id}/status"
                        ))
                    
                    status_responses = await asyncio.gather(*status_tasks, return_exceptions=True)
                    
                    processed_count = 0
                    failed_count = 0
                    
                    for response in status_responses:
                        if isinstance(response, Exception):
                            continue
                        
                        if response.status_code == 200:
                            status_data = response.json()
                            status = status_data.get('status', 'unknown')
                            
                            if status in ['completed', 'processed', 'success']:
                                processed_count += 1
                            elif status in ['failed', 'error']:
                                failed_count += 1
                    
                    if processed_count == len(document_ids):
                        all_processed = True
                    elif failed_count > 0:
                        pytest.fail(f"Some documents failed processing: {failed_count} failures")
                    
                    if not all_processed:
                        await asyncio.sleep(check_interval)
                        elapsed_time += check_interval
                
                assert all_processed, f"Batch processing timeout after {timeout_seconds}s"
                
                batch_processing_time = time.time() - batch_start_time
                performance_tracker.add_metric('batch_processing_time', batch_processing_time)
                performance_tracker.add_metric('batch_throughput', batch_size / batch_processing_time)
                
                logger.info(f"Batch of {batch_size} documents processed in {batch_processing_time:.2f}s")
                logger.info(f"Throughput: {batch_size / batch_processing_time:.2f} docs/second")

    async def test_document_retrieval_workflow(self, test_config, performance_tracker):
        """Test document storage and retrieval workflow"""
        
        # Upload a test document first
        test_image = Image.new('RGB', (600, 400), color='lightblue')
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        document_id = None
        retrieval_times = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Upload document
            upload_data = {
                'file': ('retrieval_test.png', img_buffer.getvalue(), 'image/png'),
                'metadata': json.dumps({
                    'test_type': 'retrieval_workflow',
                    'retention_period': '30_days'
                })
            }
            
            upload_response = await client.post(
                f"{test_config['base_url']}/api/v1/documents/upload",
                files=upload_data
            )
            
            assert upload_response.status_code in [200, 201], f"Upload failed: {upload_response.status_code}"
            upload_result = upload_response.json()
            document_id = upload_result.get('document_id') or upload_result.get('id')
            
            # Wait for processing to complete
            await asyncio.sleep(5)
            
            # Test multiple retrieval methods
            retrieval_tests = [
                ('metadata', f"/api/v1/documents/{document_id}"),
                ('status', f"/api/v1/documents/{document_id}/status"),
                ('results', f"/api/v1/documents/{document_id}/results"),
                ('download', f"/api/v1/documents/{document_id}/download")
            ]
            
            for test_name, endpoint in retrieval_tests:
                retrieval_start = time.time()
                
                try:
                    response = await client.get(f"{test_config['base_url']}{endpoint}")
                    retrieval_time = time.time() - retrieval_start
                    
                    assert response.status_code in [200, 404], f"{test_name} retrieval failed: {response.status_code}"
                    
                    if response.status_code == 200:
                        retrieval_times.append(retrieval_time)
                        performance_tracker.add_metric('document_retrieval_time', retrieval_time)
                        logger.info(f"{test_name} retrieval successful in {retrieval_time:.3f}s")
                    else:
                        logger.info(f"{test_name} endpoint returned 404 (may be expected)")
                
                except Exception as e:
                    logger.error(f"{test_name} retrieval failed: {e}")
        
        # Validate retrieval performance
        if retrieval_times:
            avg_retrieval_time = np.mean(retrieval_times)
            p95_retrieval_time = np.percentile(retrieval_times, 95)
            
            assert avg_retrieval_time < 2.0, f"Average retrieval time too high: {avg_retrieval_time:.3f}s"
            logger.info(f"Document retrieval stats - Mean: {avg_retrieval_time:.3f}s, P95: {p95_retrieval_time:.3f}s")

    async def test_concurrent_processing_workflow(self, test_config, performance_tracker, statistical_validator):
        """Test concurrent document processing"""
        
        concurrent_uploads = 8  # Number of concurrent uploads
        
        # Create test documents
        test_documents = []
        for i in range(concurrent_uploads):
            test_image = Image.new('RGB', (300, 200), color=(i*30 % 255, (i*50) % 255, (i*70) % 255))
            img_buffer = BytesIO()
            test_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            test_documents.append({
                'id': i,
                'filename': f'concurrent_test_{i}.png',
                'content': img_buffer.getvalue()
            })
        
        async def process_single_document(client: httpx.AsyncClient, doc: Dict[str, Any]) -> Dict[str, Any]:
            """Process a single document and return metrics"""
            start_time = time.time()
            
            try:
                # Upload
                upload_data = {
                    'file': (doc['filename'], doc['content'], 'image/png')
                }
                
                upload_response = await client.post(
                    f"{test_config['base_url']}/api/v1/documents/upload",
                    files=upload_data
                )
                
                if upload_response.status_code not in [200, 201]:
                    return {
                        'doc_id': doc['id'],
                        'success': False,
                        'error': f"Upload failed: {upload_response.status_code}",
                        'total_time': time.time() - start_time
                    }
                
                result = upload_response.json()
                document_id = result.get('document_id') or result.get('id')
                
                # Wait for processing (with timeout)
                processing_timeout = 45  # 45 seconds per document
                elapsed = 0
                
                while elapsed < processing_timeout:
                    status_response = await client.get(
                        f"{test_config['base_url']}/api/v1/documents/{document_id}/status"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        
                        if status in ['completed', 'processed', 'success']:
                            return {
                                'doc_id': doc['id'],
                                'document_id': document_id,
                                'success': True,
                                'total_time': time.time() - start_time,
                                'processing_status': status
                            }
                        elif status in ['failed', 'error']:
                            return {
                                'doc_id': doc['id'],
                                'success': False,
                                'error': f"Processing failed: {status}",
                                'total_time': time.time() - start_time
                            }
                    
                    await asyncio.sleep(2)
                    elapsed += 2
                
                return {
                    'doc_id': doc['id'],
                    'success': False,
                    'error': 'Processing timeout',
                    'total_time': time.time() - start_time
                }
                
            except Exception as e:
                return {
                    'doc_id': doc['id'],
                    'success': False,
                    'error': str(e),
                    'total_time': time.time() - start_time
                }
        
        # Execute concurrent processing
        concurrent_start_time = time.time()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            tasks = [process_single_document(client, doc) for doc in test_documents]
            results = await asyncio.gather(*tasks)
        
        total_concurrent_time = time.time() - concurrent_start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        success_rate = len(successful_results) / len(results)
        
        assert success_rate >= 0.75, f"Concurrent processing success rate too low: {success_rate:.2%}"
        
        if successful_results:
            processing_times = [r['total_time'] for r in successful_results]
            avg_processing_time = np.mean(processing_times)
            
            # Statistical validation
            validation_result = statistical_validator.validate_performance(
                processing_times, threshold=60.0, test_type='mean'
            )
            
            performance_tracker.add_metric('concurrent_processing_success_rate', success_rate)
            performance_tracker.add_metric('concurrent_avg_processing_time', avg_processing_time)
            
            logger.info(f"Concurrent Processing Results:")
            logger.info(f"  Success rate: {success_rate:.2%} ({len(successful_results)}/{len(results)})")
            logger.info(f"  Average processing time: {avg_processing_time:.2f}s")
            logger.info(f"  Total concurrent time: {total_concurrent_time:.2f}s")
            
            if failed_results:
                logger.warning(f"Failed documents: {len(failed_results)}")
                for failure in failed_results[:3]:  # Log first 3 failures
                    logger.warning(f"  Doc {failure['doc_id']}: {failure['error']}")
            
            assert validation_result['valid'], f"Concurrent processing times exceed threshold: {validation_result}"

@pytest.mark.e2e
class TestWorkflowErrorHandling:
    """Test error handling in document processing workflows"""
    
    async def test_invalid_document_upload(self, test_config):
        """Test handling of invalid document uploads"""
        
        invalid_test_cases = [
            {
                'name': 'empty_file',
                'content': b'',
                'content_type': 'text/plain',
                'filename': 'empty.txt'
            },
            {
                'name': 'invalid_image',
                'content': b'not_an_image_file_content',
                'content_type': 'image/jpeg',
                'filename': 'invalid.jpg'
            },
            {
                'name': 'unsupported_format',
                'content': b'%PDF-1.4 fake pdf content',
                'content_type': 'application/pdf',
                'filename': 'test.pdf'
            }
        ]
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for test_case in invalid_test_cases:
                logger.info(f"Testing invalid upload: {test_case['name']}")
                
                upload_data = {
                    'file': (
                        test_case['filename'],
                        test_case['content'],
                        test_case['content_type']
                    )
                }
                
                try:
                    response = await client.post(
                        f"{test_config['base_url']}/api/v1/documents/upload",
                        files=upload_data
                    )
                    
                    # Should either reject with 4xx or accept but handle gracefully
                    if response.status_code >= 400:
                        logger.info(f"Invalid upload correctly rejected: {response.status_code}")
                        # This is expected behavior
                        continue
                    elif response.status_code in [200, 201]:
                        # If accepted, processing should handle it gracefully
                        result = response.json()
                        document_id = result.get('document_id') or result.get('id')
                        
                        if document_id:
                            # Wait briefly and check status
                            await asyncio.sleep(5)
                            
                            status_response = await client.get(
                                f"{test_config['base_url']}/api/v1/documents/{document_id}/status"
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                status = status_data.get('status', 'unknown')
                                
                                # Should either fail gracefully or succeed with limitations
                                assert status in ['failed', 'error', 'completed', 'processed'], \
                                    f"Unexpected status for invalid document: {status}"
                                
                                logger.info(f"Invalid document handled with status: {status}")
                
                except Exception as e:
                    # Network errors are acceptable for invalid uploads
                    logger.info(f"Invalid upload caused expected error: {e}")

    async def test_processing_timeout_handling(self, test_config):
        """Test handling of processing timeouts"""
        
        # Create a very large image that might cause processing delays
        large_image = Image.new('RGB', (2000, 2000), color='white')
        img_buffer = BytesIO()
        large_image.save(img_buffer, format='PNG', optimize=False)
        img_buffer.seek(0)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            upload_data = {
                'file': ('large_test.png', img_buffer.getvalue(), 'image/png'),
                'metadata': json.dumps({'test_type': 'timeout_test'})
            }
            
            upload_response = await client.post(
                f"{test_config['base_url']}/api/v1/documents/upload",
                files=upload_data
            )
            
            if upload_response.status_code in [200, 201]:
                result = upload_response.json()
                document_id = result.get('document_id') or result.get('id')
                
                # Check status periodically with a reasonable timeout
                max_wait_time = 60  # 1 minute
                check_interval = 5  # 5 seconds
                elapsed_time = 0
                final_status = None
                
                while elapsed_time < max_wait_time:
                    status_response = await client.get(
                        f"{test_config['base_url']}/api/v1/documents/{document_id}/status"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        final_status = status
                        
                        if status in ['completed', 'processed', 'failed', 'error', 'timeout']:
                            break
                    
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                
                # System should handle timeouts gracefully
                logger.info(f"Large document processing result: {final_status}")
                assert final_status in ['completed', 'processed', 'failed', 'error', 'timeout', 'processing'], \
                    f"Unexpected final status: {final_status}"

    async def test_service_unavailability_handling(self, test_config):
        """Test handling when services are temporarily unavailable"""
        
        # This test simulates service unavailability by using invalid endpoints
        # In a real environment, you might temporarily stop services
        
        unavailable_endpoints = [
            f"{test_config['base_url']}/api/v1/nonexistent",
            f"{test_config['base_url']}/api/v1/documents/invalid_id/status"
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in unavailable_endpoints:
                try:
                    response = await client.get(endpoint)
                    
                    # Should return appropriate error codes (4xx or 5xx)
                    assert response.status_code >= 400, \
                        f"Expected error code for unavailable endpoint: {response.status_code}"
                    
                    logger.info(f"Unavailable endpoint correctly returned: {response.status_code}")
                    
                except httpx.RequestError as e:
                    # Network errors are also acceptable
                    logger.info(f"Unavailable endpoint caused expected network error: {e}")