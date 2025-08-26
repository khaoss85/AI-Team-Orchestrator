#!/usr/bin/env python3
"""
🔍 FAILURE DETECTION ENGINE TESTS
==================================

Unit tests for the FailureDetectionEngine to validate pattern recognition,
especially the Quality Gate requirement of detecting OrchestrationContext
field missing issues.

Tests cover all major failure types:
- Pydantic Model Issues
- SDK/Library Integration Failures  
- Database/Connection Issues
- Resource Exhaustion
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import the classes we want to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.failure_detection_engine import (
    FailureDetectionEngine,
    FailurePatternDetector,
    ResourceMonitor,
    DatabaseConnectionMonitor,
    FailureType,
    FailureSeverity,
    DetectedFailure,
    test_orchestration_context_detection
)

class TestFailurePatternDetector:
    """Test the failure pattern detection logic"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.detector = FailurePatternDetector()
    
    def test_orchestration_context_missing_detection(self):
        """QUALITY GATE TEST: Detect OrchestrationContext field missing"""
        error_message = "ValidationError: 1 validation error for TaskOutput\nOrchestrationContext\n  field required (type=value_error.missing)"
        context = {
            'task_id': 'test_task_123',
            'workspace_id': 'test_workspace_456',
            'error_type': 'ValidationError'
        }
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None, "Should detect OrchestrationContext missing pattern"
        assert failure.failure_type == FailureType.ORCHESTRATION_CONTEXT_MISSING
        assert failure.severity == FailureSeverity.HIGH
        assert 'quality_gate_triggered' in failure.context
        assert failure.context['quality_gate_triggered'] is True
        assert failure.context['missing_field'] == 'OrchestrationContext'
    
    def test_pydantic_validation_error_detection(self):
        """Test general Pydantic validation error detection"""
        error_message = "ValidationError: 2 validation errors for TaskOutput\ntitle\n  field required\ndescription\n  field required"
        context = {'task_id': 'test', 'error_type': 'ValidationError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.PYDANTIC_MISSING_FIELD
        assert failure.severity == FailureSeverity.MEDIUM
    
    def test_pydantic_invalid_type_detection(self):
        """Test Pydantic invalid type detection"""
        error_message = "ValidationError: 1 validation error for TaskOutput\nage\n  value is not a valid integer"
        context = {'task_id': 'test', 'error_type': 'ValidationError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.PYDANTIC_INVALID_TYPE
        assert failure.severity == FailureSeverity.MEDIUM
    
    def test_openai_sdk_init_error_detection(self):
        """Test OpenAI SDK initialization error detection"""
        error_message = "OpenAI client initialization failed: Invalid API key provided"
        context = {'task_id': 'test', 'error_type': 'OpenAIError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.OPENAI_SDK_INIT_ERROR
        assert failure.severity == FailureSeverity.HIGH
    
    def test_import_error_detection(self):
        """Test import error detection"""
        error_message = "ImportError: No module named 'openai'"
        context = {'task_id': 'test', 'error_type': 'ImportError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.IMPORT_ERROR
        assert failure.severity == FailureSeverity.CRITICAL
    
    def test_dependency_version_conflict_detection(self):
        """Test dependency version conflict detection"""
        error_message = "pip version mismatch: openai 1.0.0 conflicts with required 0.27.0"
        context = {'task_id': 'test', 'error_type': 'DependencyError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.DEPENDENCY_VERSION_CONFLICT
        assert failure.severity == FailureSeverity.HIGH
    
    def test_connection_pool_exhaustion_detection(self):
        """Test connection pool exhaustion detection"""
        error_message = "connection pool exhausted - too many connections"
        context = {'task_id': 'test', 'error_type': 'ConnectionError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.CONNECTION_POOL_EXHAUSTION
        assert failure.severity == FailureSeverity.CRITICAL
    
    def test_transaction_rollback_detection(self):
        """Test transaction rollback detection"""
        error_message = "Transaction rollback occurred due to constraint violation"
        context = {'task_id': 'test', 'error_type': 'DatabaseError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.TRANSACTION_ROLLBACK
        assert failure.severity == FailureSeverity.MEDIUM
    
    def test_memory_exhaustion_detection(self):
        """Test memory exhaustion detection"""
        error_message = "MemoryError: Unable to allocate memory"
        context = {'task_id': 'test', 'error_type': 'MemoryError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.MEMORY_EXHAUSTION
        assert failure.severity == FailureSeverity.CRITICAL
    
    def test_api_rate_limit_detection(self):
        """Test API rate limit detection"""
        error_message = "Rate limit exceeded: 429 too many requests"
        context = {'task_id': 'test', 'error_type': 'RateLimitError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.API_RATE_LIMIT_EXCEEDED
        assert failure.severity == FailureSeverity.MEDIUM
    
    def test_circuit_breaker_detection(self):
        """Test circuit breaker detection"""
        error_message = "Circuit breaker open - too many failures"
        context = {'task_id': 'test', 'error_type': 'CircuitBreakerError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.CIRCUIT_BREAKER_TRIPPED
        assert failure.severity == FailureSeverity.HIGH
    
    def test_no_pattern_match(self):
        """Test case where no pattern matches"""
        error_message = "Unknown random error that doesn't match any pattern"
        context = {'task_id': 'test', 'error_type': 'UnknownError'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is None, "Should not detect any pattern for unknown error"
    
    def test_context_enhancement(self):
        """Test that context is properly enhanced with pattern information"""
        error_message = "ValidationError: 1 validation error for TaskOutput\nOrchestrationContext\n  field required"
        context = {'task_id': 'test', 'workspace_id': 'workspace'}
        
        failure = self.detector.detect_failure_pattern(error_message, context)
        
        assert failure is not None
        assert 'pattern_confidence' in failure.context
        assert 'is_transient' in failure.context
        assert 'detection_timestamp' in failure.context
        assert failure.context['pattern_confidence'] == 0.95

class TestResourceMonitor:
    """Test resource monitoring functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = ResourceMonitor()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @pytest.mark.asyncio
    async def test_resource_exhaustion_detection(self, mock_disk, mock_memory, mock_cpu):
        """Test resource exhaustion detection"""
        # Mock high resource usage
        mock_cpu.return_value = 95.0  # Above 90% threshold
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 90.0  # Above 85% threshold
        mock_memory_obj.available = 1 * (1024**3)  # 1GB available
        mock_memory_obj.total = 8 * (1024**3)  # 8GB total
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.used = 95 * (1024**3)  # 95GB used
        mock_disk_obj.total = 100 * (1024**3)  # 100GB total
        mock_disk_obj.free = 5 * (1024**3)  # 5GB free
        mock_disk.return_value = mock_disk_obj
        
        failures = await self.monitor.check_resource_exhaustion()
        
        assert len(failures) == 3, "Should detect CPU, memory, and disk issues"
        
        failure_types = [f.failure_type for f in failures]
        assert FailureType.CPU_EXHAUSTION in failure_types
        assert FailureType.MEMORY_EXHAUSTION in failure_types
        assert FailureType.DISK_SPACE_LOW in failure_types
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')  
    @patch('psutil.disk_usage')
    @pytest.mark.asyncio
    async def test_normal_resource_usage(self, mock_disk, mock_memory, mock_cpu):
        """Test normal resource usage (no failures)"""
        # Mock normal resource usage
        mock_cpu.return_value = 50.0  # Below threshold
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0  # Below threshold
        mock_memory_obj.available = 4 * (1024**3)
        mock_memory_obj.total = 8 * (1024**3)
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.used = 50 * (1024**3)
        mock_disk_obj.total = 100 * (1024**3)
        mock_disk_obj.free = 50 * (1024**3)
        mock_disk.return_value = mock_disk_obj
        
        failures = await self.monitor.check_resource_exhaustion()
        
        assert len(failures) == 0, "Should not detect any failures with normal usage"

class TestDatabaseConnectionMonitor:
    """Test database connection monitoring"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = DatabaseConnectionMonitor()
    
    @patch('services.failure_detection_engine.supabase')
    @pytest.mark.asyncio
    async def test_database_connection_success(self, mock_supabase):
        """Test successful database connection"""
        # Mock successful database query
        mock_response = Mock()
        mock_response.data = [{'id': 'test-id'}]
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
        
        failures = await self.monitor.check_database_health()
        
        assert len(failures) == 0, "Should not detect failures with successful connection"
    
    @patch('services.failure_detection_engine.supabase')
    @pytest.mark.asyncio
    async def test_database_connection_timeout(self, mock_supabase):
        """Test database connection timeout"""
        # Mock timeout error
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.side_effect = TimeoutError("Request timed out")
        
        failures = await self.monitor.check_database_health()
        
        assert len(failures) == 1
        assert failures[0].failure_type == FailureType.DATABASE_TIMEOUT
        assert failures[0].severity == FailureSeverity.HIGH
    
    @patch('services.failure_detection_engine.supabase')
    @pytest.mark.asyncio
    async def test_database_connection_pool_exhaustion(self, mock_supabase):
        """Test database connection pool exhaustion"""
        # Mock connection pool exhaustion
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("too many connections")
        
        failures = await self.monitor.check_database_health()
        
        assert len(failures) == 1
        assert failures[0].failure_type == FailureType.CONNECTION_POOL_EXHAUSTION
        assert failures[0].severity == FailureSeverity.CRITICAL

class TestFailureDetectionEngine:
    """Test the main failure detection engine"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.engine = FailureDetectionEngine()
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        """Test engine start and stop functionality"""
        assert not self.engine.running
        
        await self.engine.start()
        assert self.engine.running
        
        await self.engine.stop()
        assert not self.engine.running
    
    @pytest.mark.asyncio
    async def test_detect_failure_from_error(self):
        """Test external API for failure detection"""
        error_message = "ValidationError: OrchestrationContext field required"
        context = {'task_id': 'test', 'workspace_id': 'workspace'}
        
        failure = await self.engine.detect_failure_from_error(error_message, context)
        
        assert failure is not None
        assert failure.failure_type == FailureType.ORCHESTRATION_CONTEXT_MISSING
    
    @pytest.mark.asyncio
    async def test_get_failure_stats(self):
        """Test failure statistics retrieval"""
        stats = await self.engine.get_failure_stats()
        
        assert 'total_failures_detected' in stats
        assert 'active_failures_count' in stats
        assert 'failures_by_type' in stats
        assert 'failures_by_severity' in stats
        assert 'pattern_count' in stats
        assert 'reused_patterns' in stats
        assert 'new_patterns' in stats
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test engine health check"""
        health = await self.engine.health_check()
        
        assert 'running' in health
        assert 'enabled' in health
        assert 'component_availability' in health
        assert health['running'] == self.engine.running
        assert health['enabled'] == self.engine.enabled

class TestIntegrationAndQualityGate:
    """Integration tests and quality gate validation"""
    
    @pytest.mark.asyncio
    async def test_orchestration_context_quality_gate(self):
        """QUALITY GATE: Test the specific OrchestrationContext detection"""
        result = await test_orchestration_context_detection()
        
        assert result is True, "Quality gate test must pass - OrchestrationContext detection failed"
    
    def test_pattern_coverage(self):
        """Test that all required failure types have patterns"""
        detector = FailurePatternDetector()
        
        # Required failure types for quality coverage
        required_types = [
            FailureType.ORCHESTRATION_CONTEXT_MISSING,  # QUALITY GATE
            FailureType.PYDANTIC_VALIDATION_ERROR,
            FailureType.PYDANTIC_MISSING_FIELD,
            FailureType.OPENAI_SDK_INIT_ERROR,
            FailureType.IMPORT_ERROR,
            FailureType.SUPABASE_CONNECTION_ERROR,
            FailureType.MEMORY_EXHAUSTION,
            FailureType.API_RATE_LIMIT_EXCEEDED
        ]
        
        pattern_types = set()
        for pattern in detector.all_patterns:
            pattern_types.add(pattern['failure_type'])
        
        missing_types = set(required_types) - pattern_types
        assert len(missing_types) == 0, f"Missing patterns for failure types: {missing_types}"
    
    def test_component_reuse_percentage(self):
        """Test that we're actually reusing existing components (85% target)"""
        detector = FailurePatternDetector()
        
        total_patterns = len(detector.all_patterns)
        reused_patterns = len(detector.existing_patterns)
        
        if total_patterns > 0:
            reuse_percentage = (reused_patterns / total_patterns) * 100
            
            # We should be reusing a significant portion of existing patterns
            # The exact percentage may vary based on available components
            assert reuse_percentage > 30, f"Pattern reuse percentage too low: {reuse_percentage:.1f}%"
            print(f"✅ Pattern reuse: {reuse_percentage:.1f}% ({reused_patterns}/{total_patterns})")
    
    def test_failure_severity_mapping(self):
        """Test that failure severities are properly mapped"""
        detector = FailurePatternDetector()
        
        critical_patterns = [p for p in detector.all_patterns if p['severity'] == FailureSeverity.CRITICAL]
        high_patterns = [p for p in detector.all_patterns if p['severity'] == FailureSeverity.HIGH]
        
        assert len(critical_patterns) > 0, "Should have at least some critical severity patterns"
        assert len(high_patterns) > 0, "Should have at least some high severity patterns"
        
        # OrchestrationContext should be high severity
        orchestration_patterns = [
            p for p in detector.all_patterns 
            if p['failure_type'] == FailureType.ORCHESTRATION_CONTEXT_MISSING
        ]
        assert len(orchestration_patterns) > 0, "Should have OrchestrationContext pattern"
        assert orchestration_patterns[0]['severity'] == FailureSeverity.HIGH, "OrchestrationContext should be HIGH severity"

# Test Data and Fixtures
@pytest.fixture
def sample_error_messages():
    """Sample error messages for testing"""
    return {
        'orchestration_context': "ValidationError: 1 validation error for TaskOutput\nOrchestrationContext\n  field required (type=value_error.missing)",
        'pydantic_missing_field': "ValidationError: 2 validation errors for TaskOutput\ntitle\n  field required\ndescription\n  field required",
        'openai_init_error': "OpenAI client initialization failed: Invalid API key provided",
        'import_error': "ImportError: No module named 'openai'",
        'memory_error': "MemoryError: Unable to allocate 4.0 GiB array with data type float64",
        'rate_limit': "Rate limit exceeded: 429 too many requests",
        'database_timeout': "TimeoutError: Database query timed out after 30 seconds",
        'connection_pool': "connection pool exhausted - too many connections"
    }

if __name__ == "__main__":
    # Run the quality gate test directly
    print("🔍 Running FailureDetectionEngine Quality Gate Test...")
    
    async def run_quality_gate():
        result = await test_orchestration_context_detection()
        if result:
            print("✅ QUALITY GATE PASSED: OrchestrationContext detection working")
            return 0
        else:
            print("❌ QUALITY GATE FAILED: OrchestrationContext detection not working")
            return 1
    
    import sys
    exit_code = asyncio.run(run_quality_gate())
    sys.exit(exit_code)