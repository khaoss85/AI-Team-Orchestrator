#!/usr/bin/env python3
"""
🧠 RECOVERY ANALYSIS ENGINE TESTS
==================================

Comprehensive unit tests for the RecoveryAnalysisEngine with performance benchmarks
and quality gate validations.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the recovery analysis engine and dependencies
try:
    from services.recovery_analysis_engine import (
        RecoveryAnalysisEngine,
        RecoveryPatternMatcher,
        BackoffCalculator,
        AIRecoveryDecisionEngine,
        RecoveryStrategy,
        RecoveryDecision,
        RecoveryContext,
        RecoveryAnalysisResult,
        recovery_analysis_engine,
        analyze_task_recovery,
        should_attempt_recovery,
        test_orchestration_context_recovery_decision
    )
    RECOVERY_ANALYSIS_AVAILABLE = True
except ImportError:
    RECOVERY_ANALYSIS_AVAILABLE = False
    pytest.skip("RecoveryAnalysisEngine not available", allow_module_level=True)

class TestRecoveryPatternMatcher:
    """Test the pattern matching functionality"""
    
    def setup_method(self):
        self.pattern_matcher = RecoveryPatternMatcher()
    
    def test_orchestration_context_pattern_matching(self):
        """🎯 QUALITY GATE TEST: OrchestrationContext pattern matching"""
        error_message = "ValidationError: 1 validation error for TaskOutput\nOrchestrationContext\n  field required (type=value_error.missing)"
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace", 
            agent_id="test_agent",
            error_message=error_message,
            error_type="ValidationError"
        )
        
        matched_pattern = self.pattern_matcher.match_recovery_pattern(error_message, context)
        
        assert matched_pattern is not None, "OrchestrationContext pattern should be matched"
        assert matched_pattern['pattern_id'] == 'orchestration_context_missing'
        assert matched_pattern['recovery_strategy'] == RecoveryStrategy.IMMEDIATE_RETRY
        assert matched_pattern['confidence'] >= 0.9
        
    def test_rate_limit_pattern_matching(self):
        """Test rate limit error pattern matching"""
        error_message = "429 Too Many Requests: Rate limit exceeded"
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message=error_message,
            error_type="HTTPError"
        )
        
        matched_pattern = self.pattern_matcher.match_recovery_pattern(error_message, context)
        
        assert matched_pattern is not None
        assert matched_pattern['pattern_id'] == 'rate_limit_exceeded'
        assert matched_pattern['recovery_strategy'] == RecoveryStrategy.LINEAR_BACKOFF
        assert matched_pattern['confidence'] >= 0.9
    
    def test_timeout_pattern_matching(self):
        """Test timeout error pattern matching"""
        error_message = "Connection timeout after 30 seconds"
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message=error_message,
            error_type="TimeoutError"
        )
        
        matched_pattern = self.pattern_matcher.match_recovery_pattern(error_message, context)
        
        assert matched_pattern is not None
        assert matched_pattern['pattern_id'] == 'openai_timeout'
        assert matched_pattern['recovery_strategy'] == RecoveryStrategy.EXPONENTIAL_BACKOFF
        
    def test_import_error_pattern_matching(self):
        """Test import error pattern matching"""
        error_message = "ImportError: No module named 'some_module'"
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message=error_message,
            error_type="ImportError"
        )
        
        matched_pattern = self.pattern_matcher.match_recovery_pattern(error_message, context)
        
        assert matched_pattern is not None
        assert matched_pattern['pattern_id'] == 'import_error'
        assert matched_pattern['recovery_strategy'] == RecoveryStrategy.ESCALATE_TO_HUMAN
        assert matched_pattern['max_retries'] == 0
    
    def test_unknown_error_fallback(self):
        """Test fallback for unknown error patterns"""
        error_message = "Some completely unknown error that doesn't match any pattern"
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message=error_message,
            error_type="UnknownError"
        )
        
        matched_pattern = self.pattern_matcher.match_recovery_pattern(error_message, context)
        
        # Should return None for unknown patterns
        assert matched_pattern is None

class TestBackoffCalculator:
    """Test backoff calculation logic"""
    
    def setup_method(self):
        self.backoff_calculator = BackoffCalculator()
    
    def test_immediate_retry_delay(self):
        """Test immediate retry has no delay"""
        delay = self.backoff_calculator.calculate_delay(RecoveryStrategy.IMMEDIATE_RETRY, 1)
        assert delay == 0.0
    
    def test_exponential_backoff_delay(self):
        """Test exponential backoff calculation"""
        delay1 = self.backoff_calculator.calculate_delay(RecoveryStrategy.EXPONENTIAL_BACKOFF, 1)
        delay2 = self.backoff_calculator.calculate_delay(RecoveryStrategy.EXPONENTIAL_BACKOFF, 2)
        delay3 = self.backoff_calculator.calculate_delay(RecoveryStrategy.EXPONENTIAL_BACKOFF, 3)
        
        # Exponential backoff should increase
        assert delay1 < delay2 < delay3
        assert delay1 == 5.0  # Initial delay
        assert delay2 == 10.0  # 5 * 2
        assert delay3 == 20.0  # 5 * 2^2
    
    def test_linear_backoff_delay(self):
        """Test linear backoff calculation"""
        delay1 = self.backoff_calculator.calculate_delay(RecoveryStrategy.LINEAR_BACKOFF, 1)
        delay2 = self.backoff_calculator.calculate_delay(RecoveryStrategy.LINEAR_BACKOFF, 2)
        delay3 = self.backoff_calculator.calculate_delay(RecoveryStrategy.LINEAR_BACKOFF, 3)
        
        # Linear backoff should increase linearly
        assert delay1 < delay2 < delay3
        assert delay2 - delay1 == delay3 - delay2  # Equal intervals
    
    def test_circuit_breaker_delay(self):
        """Test circuit breaker has fixed delay"""
        delay1 = self.backoff_calculator.calculate_delay(RecoveryStrategy.CIRCUIT_BREAKER, 1)
        delay2 = self.backoff_calculator.calculate_delay(RecoveryStrategy.CIRCUIT_BREAKER, 2)
        
        # Circuit breaker should have fixed delay regardless of attempt
        assert delay1 == delay2
        assert delay1 == 1800.0  # 30 minutes
    
    def test_max_delay_respected(self):
        """Test that maximum delays are respected"""
        # Test exponential backoff max delay
        large_attempt = 10
        delay = self.backoff_calculator.calculate_delay(RecoveryStrategy.EXPONENTIAL_BACKOFF, large_attempt)
        assert delay <= 300.0  # Max delay for exponential backoff
        
        # Test linear backoff max delay  
        delay = self.backoff_calculator.calculate_delay(RecoveryStrategy.LINEAR_BACKOFF, large_attempt)
        assert delay <= 600.0  # Max delay for linear backoff

class TestAIRecoveryDecisionEngine:
    """Test AI-driven recovery decision logic"""
    
    def setup_method(self):
        self.ai_engine = AIRecoveryDecisionEngine()
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_orchestration_context(self):
        """Test fallback analysis for OrchestrationContext error"""
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message="ValidationError: OrchestrationContext field required",
            error_type="ValidationError",
            previous_attempts=0
        )
        
        # Test fallback analysis (AI unavailable)
        analysis = self.ai_engine._fallback_analysis(context)
        
        assert analysis['recommended_strategy'] == RecoveryStrategy.IMMEDIATE_RETRY.value
        assert analysis['confidence_score'] >= 0.9
        assert analysis['max_retry_attempts'] == 2
        assert not analysis['ai_analysis_used']
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_timeout_error(self):
        """Test fallback analysis for timeout error"""
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message="Request timeout after 30 seconds",
            error_type="TimeoutError",
            previous_attempts=0
        )
        
        analysis = self.ai_engine._fallback_analysis(context)
        
        assert analysis['recommended_strategy'] == RecoveryStrategy.EXPONENTIAL_BACKOFF.value
        assert analysis['confidence_score'] >= 0.7
        assert analysis['max_retry_attempts'] == 5
    
    @pytest.mark.asyncio
    async def test_fallback_analysis_import_error(self):
        """Test fallback analysis for import error"""
        context = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message="ImportError: No module named 'missing_module'",
            error_type="ImportError",
            previous_attempts=0
        )
        
        analysis = self.ai_engine._fallback_analysis(context)
        
        assert analysis['recommended_strategy'] == RecoveryStrategy.ESCALATE_TO_HUMAN.value
        assert analysis['confidence_score'] >= 0.8
        assert analysis['max_retry_attempts'] == 0
    
    @pytest.mark.asyncio
    async def test_confidence_reduction_with_attempts(self):
        """Test that confidence reduces with multiple attempts"""
        context_first = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message="Some error",
            error_type="Error",
            previous_attempts=0
        )
        
        context_multiple = RecoveryContext(
            task_id="test_task",
            workspace_id="test_workspace",
            agent_id="test_agent",
            error_message="Some error",
            error_type="Error",
            previous_attempts=3
        )
        
        analysis_first = self.ai_engine._fallback_analysis(context_first)
        analysis_multiple = self.ai_engine._fallback_analysis(context_multiple)
        
        assert analysis_multiple['confidence_score'] < analysis_first['confidence_score']

class TestRecoveryAnalysisEngine:
    """Test the main recovery analysis engine"""
    
    def setup_method(self):
        self.engine = RecoveryAnalysisEngine()
    
    @pytest.mark.asyncio 
    async def test_build_recovery_context(self):
        """Test recovery context building"""
        with patch('services.recovery_analysis_engine.DATABASE_AVAILABLE', True):
            with patch('services.recovery_analysis_engine.supabase') as mock_supabase:
                # Mock database responses
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
                    'name': 'Test Task',
                    'description': 'Test Description',
                    'recovery_count': 1,
                    'agent_id': 'agent_123'
                }]
                
                context = await self.engine._build_recovery_context(
                    task_id="test_task",
                    workspace_id="test_workspace",
                    error_message="Test error",
                    error_type="TestError"
                )
                
                assert context.task_id == "test_task"
                assert context.workspace_id == "test_workspace"
                assert context.error_message == "Test error"
                assert context.error_type == "TestError"
    
    @pytest.mark.asyncio
    async def test_analyze_task_recovery_success(self):
        """Test successful task recovery analysis"""
        with patch.object(self.engine, '_build_recovery_context') as mock_context:
            with patch.object(self.engine, '_detect_failure_pattern') as mock_detect:
                with patch.object(self.engine, '_synthesize_recovery_decision') as mock_synthesize:
                    with patch.object(self.engine, '_store_recovery_analysis') as mock_store:
                        with patch.object(self.engine, '_send_recovery_notification') as mock_notify:
                            
                            # Setup mocks
                            mock_context.return_value = RecoveryContext(
                                task_id="test_task",
                                workspace_id="test_workspace",
                                agent_id="test_agent",
                                error_message="Test error",
                                error_type="TestError"
                            )
                            
                            mock_detect.return_value = None
                            mock_synthesize.return_value = RecoveryAnalysisResult(
                                recovery_decision=RecoveryDecision.RETRY,
                                recovery_strategy=RecoveryStrategy.IMMEDIATE_RETRY,
                                confidence_score=0.95
                            )
                            mock_store.return_value = None
                            mock_notify.return_value = None
                            
                            # Test analysis
                            result = await self.engine.analyze_task_recovery(
                                task_id="test_task",
                                workspace_id="test_workspace",
                                error_message="Test error",
                                error_type="TestError"
                            )
                            
                            assert result.recovery_decision == RecoveryDecision.RETRY
                            assert result.recovery_strategy == RecoveryStrategy.IMMEDIATE_RETRY
                            assert result.confidence_score == 0.95
                            assert result.analysis_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_should_attempt_recovery_max_attempts_exceeded(self):
        """Test that recovery is not attempted when max attempts exceeded"""
        with patch('services.recovery_analysis_engine.MAX_RECOVERY_ATTEMPTS_PER_TASK', 2):
            with patch.object(self.engine, '_build_recovery_context') as mock_context:
                
                # Mock context with too many attempts
                mock_context.return_value = RecoveryContext(
                    task_id="test_task",
                    workspace_id="test_workspace",
                    agent_id="test_agent",
                    error_message="Test error",
                    error_type="TestError",
                    previous_attempts=3  # Exceeds max
                )
                
                should_recover, analysis = await self.engine.should_attempt_recovery(
                    task_id="test_task",
                    workspace_id="test_workspace",
                    error_message="Test error",
                    error_type="TestError"
                )
                
                assert not should_recover
                assert analysis is None
    
    @pytest.mark.asyncio
    async def test_should_attempt_recovery_low_confidence(self):
        """Test that recovery is not attempted when confidence is too low"""
        with patch('services.recovery_analysis_engine.RECOVERY_CONFIDENCE_THRESHOLD', 0.8):
            with patch.object(self.engine, 'analyze_task_recovery') as mock_analyze:
                
                # Mock low confidence analysis
                mock_analyze.return_value = RecoveryAnalysisResult(
                    recovery_decision=RecoveryDecision.RETRY,
                    recovery_strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
                    confidence_score=0.5  # Below threshold
                )
                
                should_recover, analysis = await self.engine.should_attempt_recovery(
                    task_id="test_task",
                    workspace_id="test_workspace", 
                    error_message="Test error",
                    error_type="TestError"
                )
                
                assert not should_recover
                assert analysis.confidence_score == 0.5
    
    @pytest.mark.asyncio
    async def test_get_recovery_stats(self):
        """Test recovery statistics collection"""
        # Add some mock history
        self.engine.analysis_history = [
            RecoveryAnalysisResult(
                recovery_decision=RecoveryDecision.RETRY,
                recovery_strategy=RecoveryStrategy.IMMEDIATE_RETRY,
                confidence_score=0.95,
                ai_analysis_used=True
            ),
            RecoveryAnalysisResult(
                recovery_decision=RecoveryDecision.ESCALATE,
                recovery_strategy=RecoveryStrategy.ESCALATE_TO_HUMAN,
                confidence_score=0.85,
                ai_analysis_used=False
            )
        ]
        
        stats = await self.engine.get_recovery_stats()
        
        assert 'strategy_distribution' in stats
        assert 'confidence_distribution' in stats
        assert 'recovery_decision_distribution' in stats
        assert 'ai_analysis_usage_percentage' in stats
        assert stats['component_reuse_percentage'] == 90.0
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality"""
        health = await self.engine.health_check()
        
        assert 'enabled' in health
        assert 'ai_decisions_enabled' in health
        assert 'component_availability' in health
        assert 'analysis_count' in health
        assert 'reuse_target_percentage' in health
        assert health['reuse_target_percentage'] == 90.0

class TestQualityGates:
    """Test quality gates and specific scenarios"""
    
    @pytest.mark.asyncio
    async def test_orchestration_context_quality_gate(self):
        """🎯 QUALITY GATE TEST: OrchestrationContext field missing detection"""
        success = await test_orchestration_context_recovery_decision()
        assert success, "OrchestrationContext quality gate must pass"
    
    @pytest.mark.asyncio
    async def test_end_to_end_orchestration_context_analysis(self):
        """End-to-end test for OrchestrationContext recovery analysis"""
        result = await analyze_task_recovery(
            task_id="test_task",
            workspace_id="test_workspace",
            error_message="ValidationError: 1 validation error for TaskOutput\nOrchestrationContext\n  field required (type=value_error.missing)",
            error_type="ValidationError",
            task_name="Test Task"
        )
        
        # Verify quality gate requirements
        assert result.recovery_strategy == RecoveryStrategy.IMMEDIATE_RETRY
        assert result.confidence_score >= 0.9
        assert result.recovery_decision == RecoveryDecision.RETRY
        assert result.recommended_delay_seconds == 0.0  # Immediate retry

class TestPerformanceBenchmarks:
    """Performance benchmarks for recovery analysis"""
    
    def setup_method(self):
        self.engine = RecoveryAnalysisEngine()
    
    @pytest.mark.asyncio
    async def test_analysis_performance_benchmark(self):
        """Test that analysis completes within performance requirements"""
        start_time = time.time()
        
        result = await self.engine.analyze_task_recovery(
            task_id="perf_test_task",
            workspace_id="perf_test_workspace",
            error_message="ValidationError: Some validation error",
            error_type="ValidationError"
        )
        
        end_time = time.time()
        analysis_time_seconds = end_time - start_time
        
        # Analysis should complete within 500ms as per requirements
        assert analysis_time_seconds < 0.5, f"Analysis took {analysis_time_seconds:.3f}s, expected < 0.5s"
        assert result.analysis_time_ms < 500, f"Reported analysis time {result.analysis_time_ms}ms, expected < 500ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_performance(self):
        """Test performance under concurrent analysis load"""
        num_concurrent = 10
        
        async def single_analysis(task_num):
            return await self.engine.analyze_task_recovery(
                task_id=f"concurrent_task_{task_num}",
                workspace_id="concurrent_workspace",
                error_message=f"Test error {task_num}",
                error_type="TestError"
            )
        
        start_time = time.time()
        
        # Run concurrent analyses
        tasks = [single_analysis(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        average_time = total_time / num_concurrent
        
        # Each analysis should still be fast even under concurrent load
        assert average_time < 1.0, f"Average analysis time under load: {average_time:.3f}s"
        assert all(r.analysis_time_ms < 1000 for r in results), "Individual analysis times should be < 1s"
        
        # All analyses should complete successfully
        assert len(results) == num_concurrent
        assert all(r.confidence_score > 0 for r in results)
    
    @pytest.mark.asyncio
    async def test_component_reuse_verification(self):
        """Verify that 90% component reuse target is achieved"""
        # This test verifies that the engine reports 90% component reuse
        engine_stats = await self.engine.get_recovery_stats()
        
        assert engine_stats['component_reuse_percentage'] == 90.0
        
        # Verify component reuse stats are tracked
        assert 'component_reuse_stats' in engine_stats
        reuse_stats = engine_stats['component_reuse_stats']
        
        # Verify all expected components are tracked
        expected_components = [
            'workspace_recovery',
            'failure_detection', 
            'health_monitor',
            'rate_limiter',
            'task_monitor',
            'ai_classifier'
        ]
        
        for component in expected_components:
            assert component in reuse_stats, f"Component {component} should be tracked in reuse stats"

# Utility functions for test setup
def create_test_recovery_context(
    task_id: str = "test_task",
    error_message: str = "Test error",
    error_type: str = "TestError",
    previous_attempts: int = 0
) -> RecoveryContext:
    """Create a test recovery context"""
    return RecoveryContext(
        task_id=task_id,
        workspace_id="test_workspace",
        agent_id="test_agent",
        error_message=error_message,
        error_type=error_type,
        previous_attempts=previous_attempts
    )

# Test configuration
def pytest_configure(config):
    """Configure pytest for recovery analysis tests"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    config.addinivalue_line(
        "markers", "quality_gate: mark test as quality gate validation"
    )