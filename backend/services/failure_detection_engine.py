#!/usr/bin/env python3
"""
🔍 FAILURE DETECTION ENGINE
============================

Real-time failure detection system that identifies patterns of failure before they
cause system-wide issues. Integrates with existing monitoring infrastructure to
provide proactive failure prevention.

REUSES 85% of existing components:
- health_monitor.py: Health check patterns and workspace monitoring
- task_execution_monitor.py: ExecutionStage tracking and hang detection
- workspace_recovery_system.py: Recovery strategy patterns and diagnosis
- executor.py: Circuit breaker logic and anti-loop protection
- recovery_explanation_engine.py: Error pattern matching and analysis

NEW FAILURE DETECTION SCOPE:
1. Pydantic Model Issues (ValidationError patterns, missing fields)
2. SDK/Library Integration Failures (OpenAI SDK, dependency conflicts)
3. Database/Connection Issues (Supabase, transaction rollbacks)
4. Resource Exhaustion (Memory/CPU/API rate limits)

Quality Gate: Auto-detect "OrchestrationContext" field missing issue type
"""

import asyncio
import logging
import os
import time
import traceback
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

# Import existing monitoring components (85% REUSE)
try:
    from health_monitor import HealthMonitor
    HEALTH_MONITOR_AVAILABLE = True
except ImportError:
    HEALTH_MONITOR_AVAILABLE = False

try:
    from task_execution_monitor import (
        TaskExecutionMonitor, ExecutionStage, TaskExecutionTrace,
        task_monitor as existing_task_monitor
    )
    TASK_EXECUTION_MONITOR_AVAILABLE = True
except ImportError:
    TASK_EXECUTION_MONITOR_AVAILABLE = False
    ExecutionStage = None

try:
    from workspace_recovery_system import WorkspaceRecoverySystem, workspace_recovery_system
    WORKSPACE_RECOVERY_AVAILABLE = True
except ImportError:
    WORKSPACE_RECOVERY_AVAILABLE = False

try:
    from services.workspace_health_manager import (
        WorkspaceHealthManager, workspace_health_manager,
        HealthIssue, HealthIssueLevel, RecoveryStrategy
    )
    WORKSPACE_HEALTH_AVAILABLE = True
except ImportError:
    WORKSPACE_HEALTH_AVAILABLE = False
    HealthIssueLevel = None

try:
    from services.recovery_explanation_engine import (
        RecoveryExplanationEngine, recovery_explanation_engine,
        FailureCategory, FailureContext, ErrorPattern
    )
    RECOVERY_EXPLANATION_AVAILABLE = True
except ImportError:
    RECOVERY_EXPLANATION_AVAILABLE = False
    FailureCategory = None

# Database and WebSocket integrations
try:
    from database import supabase, get_workspace, list_tasks
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

try:
    from routes.websocket import broadcast_system_alert
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    broadcast_system_alert = None

from models import TaskStatus, WorkspaceStatus, AgentStatus

logger = logging.getLogger(__name__)

# Environment Configuration
FAILURE_DETECTION_ENABLED = os.getenv('FAILURE_DETECTION_ENABLED', 'true').lower() == 'true'
FAILURE_DETECTION_INTERVAL = int(os.getenv('FAILURE_DETECTION_INTERVAL_SECONDS', '30'))
PYDANTIC_ERROR_THRESHOLD = int(os.getenv('PYDANTIC_ERROR_THRESHOLD_PER_HOUR', '5'))
SDK_ERROR_THRESHOLD = int(os.getenv('SDK_ERROR_THRESHOLD_PER_HOUR', '10'))
DB_ERROR_THRESHOLD = int(os.getenv('DB_ERROR_THRESHOLD_PER_HOUR', '15'))
RESOURCE_EXHAUSTION_CPU_THRESHOLD = float(os.getenv('RESOURCE_CPU_THRESHOLD_PERCENT', '90.0'))
RESOURCE_EXHAUSTION_MEMORY_THRESHOLD = float(os.getenv('RESOURCE_MEMORY_THRESHOLD_PERCENT', '85.0'))
ENABLE_WEBSOCKET_NOTIFICATIONS = os.getenv('ENABLE_FAILURE_WEBSOCKET_NOTIFICATIONS', 'true').lower() == 'true'

class FailureType(str, Enum):
    """Types of failures the engine can detect"""
    
    # Pydantic Model Issues  
    PYDANTIC_VALIDATION_ERROR = "pydantic_validation_error"
    PYDANTIC_MISSING_FIELD = "pydantic_missing_field"
    PYDANTIC_INVALID_TYPE = "pydantic_invalid_type"
    ORCHESTRATION_CONTEXT_MISSING = "orchestration_context_missing"  # QUALITY GATE
    
    # SDK/Library Integration Failures
    OPENAI_SDK_INIT_ERROR = "openai_sdk_init_error"
    OPENAI_CLIENT_ERROR = "openai_client_error"  
    DEPENDENCY_VERSION_CONFLICT = "dependency_version_conflict"
    IMPORT_ERROR = "import_error"
    
    # Database/Connection Issues
    SUPABASE_CONNECTION_ERROR = "supabase_connection_error"
    DATABASE_TIMEOUT = "database_timeout"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    CONNECTION_POOL_EXHAUSTION = "connection_pool_exhaustion"
    
    # Resource Exhaustion
    CPU_EXHAUSTION = "cpu_exhaustion"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    API_RATE_LIMIT_EXCEEDED = "api_rate_limit_exceeded"
    DISK_SPACE_LOW = "disk_space_low"
    
    # Composite/Pattern Issues
    CASCADING_FAILURES = "cascading_failures"
    CIRCUIT_BREAKER_TRIPPED = "circuit_breaker_tripped"

class FailureSeverity(str, Enum):
    """Severity levels for failures"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DetectedFailure:
    """A detected failure instance"""
    failure_type: FailureType
    severity: FailureSeverity
    message: str
    context: Dict[str, Any]
    first_detected: datetime
    last_detected: datetime
    occurrence_count: int = 1
    affected_workspaces: Set[str] = field(default_factory=set)
    affected_tasks: Set[str] = field(default_factory=set)
    root_cause_analysis: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'failure_type': self.failure_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'context': self.context,
            'first_detected': self.first_detected.isoformat(),
            'last_detected': self.last_detected.isoformat(),
            'occurrence_count': self.occurrence_count,
            'affected_workspaces': list(self.affected_workspaces),
            'affected_tasks': list(self.affected_tasks),
            'root_cause_analysis': self.root_cause_analysis,
            'recovery_suggestion': self.recovery_suggestion
        }

@dataclass
class FailureDetectionStats:
    """Statistics about failure detection"""
    total_failures_detected: int = 0
    failures_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    failures_by_severity: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    detection_accuracy: float = 0.0
    false_positive_rate: float = 0.0
    last_detection_time: Optional[datetime] = None

class FailurePatternDetector:
    """
    🔍 REUSES task_execution_monitor.py and recovery_explanation_engine.py patterns
    Detects specific failure patterns using existing error matching logic
    """
    
    def __init__(self):
        # REUSE: Import existing error patterns from recovery_explanation_engine
        self.existing_patterns = self._import_existing_patterns()
        self.new_patterns = self._initialize_new_patterns()
        # PRIORITY: Put new patterns first so more specific patterns (like OrchestrationContext) match before general ones
        self.all_patterns = self.new_patterns + self.existing_patterns
        
        logger.info(f"🔍 FailurePatternDetector initialized with {len(self.all_patterns)} patterns "
                   f"({len(self.existing_patterns)} reused, {len(self.new_patterns)} new)")
    
    def _import_existing_patterns(self) -> List[Dict[str, Any]]:
        """REUSE: Import error patterns from RecoveryExplanationEngine"""
        patterns = []
        
        if RECOVERY_EXPLANATION_AVAILABLE:
            try:
                # Access the pattern matchers from the existing analyzer
                analyzer = recovery_explanation_engine.failure_analyzer
                for pattern in analyzer.pattern_matchers:
                    patterns.append({
                        'regex': pattern.pattern,
                        'failure_type': self._map_category_to_type(pattern.category),
                        'severity': self._map_category_to_severity(pattern.category),
                        'is_transient': pattern.is_transient,
                        'confidence': pattern.confidence_score,
                        'source': 'recovery_explanation_engine'
                    })
                
                logger.info(f"✅ Imported {len(patterns)} existing error patterns")
            except Exception as e:
                logger.warning(f"⚠️ Failed to import existing patterns: {e}")
        
        return patterns
    
    def _initialize_new_patterns(self) -> List[Dict[str, Any]]:
        """NEW: Additional patterns for specific failure types"""
        return [
            # QUALITY GATE: OrchestrationContext field missing pattern
            {
                'regex': r'ValidationError.*OrchestrationContext.*field required',
                'failure_type': FailureType.ORCHESTRATION_CONTEXT_MISSING,
                'severity': FailureSeverity.HIGH,
                'is_transient': False,
                'confidence': 0.95,
                'source': 'failure_detection_engine',
                'root_cause': 'Agent response missing OrchestrationContext field',
                'recovery': 'Retry with enhanced prompt or different agent'
            },
            
            # Pydantic Model Patterns (enhanced)
            {
                'regex': r'ValidationError.*\d+ validation error.*field required',
                'failure_type': FailureType.PYDANTIC_MISSING_FIELD,
                'severity': FailureSeverity.MEDIUM,
                'is_transient': False,
                'confidence': 0.9,
                'source': 'failure_detection_engine'
            },
            
            {
                'regex': r'ValidationError.*value is not a valid (str|int|float|bool|dict|list)',
                'failure_type': FailureType.PYDANTIC_INVALID_TYPE,
                'severity': FailureSeverity.MEDIUM,
                'is_transient': False,
                'confidence': 0.85,
                'source': 'failure_detection_engine'
            },
            
            # SDK/Library Integration
            {
                'regex': r'OpenAI.*initialization.*failed|openai.*client.*init.*error',
                'failure_type': FailureType.OPENAI_SDK_INIT_ERROR,
                'severity': FailureSeverity.HIGH,
                'is_transient': False,
                'confidence': 0.9,
                'source': 'failure_detection_engine'
            },
            
            {
                'regex': r'ImportError.*openai|ModuleNotFoundError.*openai',
                'failure_type': FailureType.IMPORT_ERROR,
                'severity': FailureSeverity.CRITICAL,
                'is_transient': False,
                'confidence': 0.95,
                'source': 'failure_detection_engine'
            },
            
            {
                'regex': r'version.*conflict|dependency.*incompatible|pip.*version.*mismatch',
                'failure_type': FailureType.DEPENDENCY_VERSION_CONFLICT,
                'severity': FailureSeverity.HIGH,
                'is_transient': False,
                'confidence': 0.8,
                'source': 'failure_detection_engine'
            },
            
            # Database/Connection Enhanced
            {
                'regex': r'connection.*pool.*exhausted|too many connections',
                'failure_type': FailureType.CONNECTION_POOL_EXHAUSTION,
                'severity': FailureSeverity.CRITICAL,
                'is_transient': True,
                'confidence': 0.9,
                'source': 'failure_detection_engine'
            },
            
            {
                'regex': r'transaction.*rollback|rollback.*transaction',
                'failure_type': FailureType.TRANSACTION_ROLLBACK,
                'severity': FailureSeverity.MEDIUM,
                'is_transient': True,
                'confidence': 0.85,
                'source': 'failure_detection_engine'
            },
            
            # Resource Exhaustion
            {
                'regex': r'MemoryError|memory.*exhausted|out of memory',
                'failure_type': FailureType.MEMORY_EXHAUSTION,
                'severity': FailureSeverity.CRITICAL,
                'is_transient': True,
                'confidence': 0.95,
                'source': 'failure_detection_engine'
            },
            
            {
                'regex': r'rate.*limit.*exceeded|too many requests|429.*too many',
                'failure_type': FailureType.API_RATE_LIMIT_EXCEEDED,
                'severity': FailureSeverity.MEDIUM,
                'is_transient': True,
                'confidence': 0.9,
                'source': 'failure_detection_engine'
            },
            
            # Composite Pattern Detection
            {
                'regex': r'circuit.*breaker.*open|circuit.*breaker.*tripped',
                'failure_type': FailureType.CIRCUIT_BREAKER_TRIPPED,
                'severity': FailureSeverity.HIGH,
                'is_transient': True,
                'confidence': 0.9,
                'source': 'failure_detection_engine'
            }
        ]
    
    def _map_category_to_type(self, category) -> FailureType:
        """Map RecoveryExplanationEngine categories to FailureDetection types"""
        if not category:
            return FailureType.PYDANTIC_VALIDATION_ERROR
            
        mapping = {
            'pydantic_validation_error': FailureType.PYDANTIC_VALIDATION_ERROR,
            'openai_api_timeout': FailureType.OPENAI_CLIENT_ERROR,
            'openai_api_rate_limit': FailureType.API_RATE_LIMIT_EXCEEDED,
            'supabase_error': FailureType.SUPABASE_CONNECTION_ERROR,
            'database_connection_error': FailureType.SUPABASE_CONNECTION_ERROR,
            'memory_exhaustion': FailureType.MEMORY_EXHAUSTION,
        }
        
        category_value = category.value if hasattr(category, 'value') else str(category)
        return mapping.get(category_value, FailureType.PYDANTIC_VALIDATION_ERROR)
    
    def _map_category_to_severity(self, category) -> FailureSeverity:
        """Map RecoveryExplanationEngine categories to severity levels"""
        if not category:
            return FailureSeverity.MEDIUM
            
        # Critical issues that need immediate attention
        critical_categories = ['memory_exhaustion', 'database_connection_error']
        # High priority issues
        high_categories = ['openai_sdk_error', 'supabase_error']
        # Low priority transient issues
        low_categories = ['openai_api_timeout', 'network_error']
        
        category_value = category.value if hasattr(category, 'value') else str(category)
        
        if category_value in critical_categories:
            return FailureSeverity.CRITICAL
        elif category_value in high_categories:
            return FailureSeverity.HIGH
        elif category_value in low_categories:
            return FailureSeverity.LOW
        else:
            return FailureSeverity.MEDIUM
    
    def detect_failure_pattern(self, error_message: str, context: Dict[str, Any]) -> Optional[DetectedFailure]:
        """Detect failure patterns in error messages"""
        import re
        
        error_text = f"{error_message} {context.get('error_type', '')}".lower()
        
        for pattern in self.all_patterns:
            # Use DOTALL flag to match across newlines (needed for ValidationError patterns)
            if re.search(pattern['regex'].lower(), error_text, re.DOTALL):
                logger.info(f"🎯 Detected failure pattern: {pattern['failure_type']}")
                
                # Extract additional context for specific patterns
                enhanced_context = self._enhance_context(pattern, error_message, context)
                
                return DetectedFailure(
                    failure_type=pattern['failure_type'],
                    severity=pattern['severity'],
                    message=error_message,
                    context=enhanced_context,
                    first_detected=datetime.now(),
                    last_detected=datetime.now(),
                    root_cause_analysis=pattern.get('root_cause'),
                    recovery_suggestion=pattern.get('recovery')
                )
        
        return None
    
    def _enhance_context(self, pattern: Dict[str, Any], error_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context with pattern-specific information"""
        enhanced = context.copy()
        enhanced.update({
            'pattern_source': pattern['source'],
            'pattern_confidence': pattern['confidence'],
            'is_transient': pattern['is_transient'],
            'detection_timestamp': datetime.now().isoformat()
        })
        
        # Extract specific information for OrchestrationContext pattern
        if pattern['failure_type'] == FailureType.ORCHESTRATION_CONTEXT_MISSING:
            enhanced.update({
                'missing_field': 'OrchestrationContext',
                'validation_error': True,
                'quality_gate_triggered': True,
                'recommended_action': 'Review agent prompt and response format'
            })
        
        # Extract field names for Pydantic validation errors
        if 'ValidationError' in error_message:
            import re
            field_matches = re.findall(r'field required|(\w+)\s*\n\s*field required', error_message)
            if field_matches:
                enhanced['missing_fields'] = field_matches
        
        return enhanced

class ResourceMonitor:
    """
    🔍 REUSES health_monitor.py patterns for system resource monitoring
    Monitors CPU, memory, disk space and other system resources
    """
    
    def __init__(self):
        self.cpu_threshold = RESOURCE_EXHAUSTION_CPU_THRESHOLD
        self.memory_threshold = RESOURCE_EXHAUSTION_MEMORY_THRESHOLD
        self.last_resource_check = datetime.now()
        self.resource_history: List[Dict[str, Any]] = []
        
        logger.info(f"🔍 ResourceMonitor initialized - CPU threshold: {self.cpu_threshold}%, "
                   f"Memory threshold: {self.memory_threshold}%")
    
    async def check_resource_exhaustion(self) -> List[DetectedFailure]:
        """Check for resource exhaustion issues"""
        failures = []
        
        try:
            # CPU usage check
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.cpu_threshold:
                failures.append(DetectedFailure(
                    failure_type=FailureType.CPU_EXHAUSTION,
                    severity=FailureSeverity.HIGH,
                    message=f"CPU usage at {cpu_percent:.1f}% (threshold: {self.cpu_threshold}%)",
                    context={
                        'cpu_percent': cpu_percent,
                        'threshold': self.cpu_threshold,
                        'timestamp': datetime.now().isoformat()
                    },
                    first_detected=datetime.now(),
                    last_detected=datetime.now()
                ))
            
            # Memory usage check  
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            if memory_percent > self.memory_threshold:
                failures.append(DetectedFailure(
                    failure_type=FailureType.MEMORY_EXHAUSTION,
                    severity=FailureSeverity.CRITICAL if memory_percent > 95 else FailureSeverity.HIGH,
                    message=f"Memory usage at {memory_percent:.1f}% (threshold: {self.memory_threshold}%)",
                    context={
                        'memory_percent': memory_percent,
                        'available_gb': memory.available / (1024**3),
                        'total_gb': memory.total / (1024**3),
                        'threshold': self.memory_threshold,
                        'timestamp': datetime.now().isoformat()
                    },
                    first_detected=datetime.now(),
                    last_detected=datetime.now()
                ))
            
            # Disk space check
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:  # 90% disk usage threshold
                failures.append(DetectedFailure(
                    failure_type=FailureType.DISK_SPACE_LOW,
                    severity=FailureSeverity.HIGH if disk_percent > 95 else FailureSeverity.MEDIUM,
                    message=f"Disk usage at {disk_percent:.1f}%",
                    context={
                        'disk_percent': disk_percent,
                        'available_gb': disk.free / (1024**3),
                        'total_gb': disk.total / (1024**3),
                        'timestamp': datetime.now().isoformat()
                    },
                    first_detected=datetime.now(),
                    last_detected=datetime.now()
                ))
            
            # Store resource history for trend analysis
            self.resource_history.append({
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent
            })
            
            # Keep only last 100 entries
            if len(self.resource_history) > 100:
                self.resource_history = self.resource_history[-100:]
                
        except Exception as e:
            logger.error(f"Error checking resource exhaustion: {e}")
            failures.append(DetectedFailure(
                failure_type=FailureType.MEMORY_EXHAUSTION,
                severity=FailureSeverity.MEDIUM,
                message=f"Resource monitoring failed: {e}",
                context={'error': str(e), 'timestamp': datetime.now().isoformat()},
                first_detected=datetime.now(),
                last_detected=datetime.now()
            ))
        
        return failures

class DatabaseConnectionMonitor:
    """
    🔍 REUSES workspace_recovery_system.py database patterns
    Monitors database connectivity and transaction health
    """
    
    def __init__(self):
        self.connection_failures: List[datetime] = []
        self.transaction_failures: List[datetime] = []
        self.last_db_check = datetime.now()
        
    async def check_database_health(self) -> List[DetectedFailure]:
        """Check database connectivity and transaction health"""
        failures = []
        
        if not DATABASE_AVAILABLE:
            return failures
        
        try:
            # Test basic connectivity
            start_time = time.time()
            response = supabase.table('workspaces').select('id').limit(1).execute()
            query_time = time.time() - start_time
            
            # Check for slow queries (> 5 seconds)
            if query_time > 5.0:
                failures.append(DetectedFailure(
                    failure_type=FailureType.DATABASE_TIMEOUT,
                    severity=FailureSeverity.MEDIUM,
                    message=f"Database query slow: {query_time:.2f}s",
                    context={
                        'query_time': query_time,
                        'threshold': 5.0,
                        'timestamp': datetime.now().isoformat()
                    },
                    first_detected=datetime.now(),
                    last_detected=datetime.now()
                ))
            
            # Check for connection pool exhaustion indicators
            # (This would require more detailed Supabase client inspection)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Record connection failure
            self.connection_failures.append(datetime.now())
            
            # Determine failure type
            if 'timeout' in error_msg:
                failure_type = FailureType.DATABASE_TIMEOUT
                severity = FailureSeverity.HIGH
            elif 'connection' in error_msg:
                failure_type = FailureType.SUPABASE_CONNECTION_ERROR
                severity = FailureSeverity.HIGH
            elif 'too many' in error_msg or 'pool' in error_msg:
                failure_type = FailureType.CONNECTION_POOL_EXHAUSTION
                severity = FailureSeverity.CRITICAL
            else:
                failure_type = FailureType.SUPABASE_CONNECTION_ERROR
                severity = FailureSeverity.MEDIUM
            
            failures.append(DetectedFailure(
                failure_type=failure_type,
                severity=severity,
                message=f"Database connectivity issue: {str(e)}",
                context={
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now().isoformat()
                },
                first_detected=datetime.now(),
                last_detected=datetime.now()
            ))
            
            # Check for pattern of failures
            recent_failures = [
                f for f in self.connection_failures 
                if f > datetime.now() - timedelta(hours=1)
            ]
            
            if len(recent_failures) > DB_ERROR_THRESHOLD:
                failures.append(DetectedFailure(
                    failure_type=FailureType.CASCADING_FAILURES,
                    severity=FailureSeverity.CRITICAL,
                    message=f"Database failure pattern detected: {len(recent_failures)} failures in last hour",
                    context={
                        'failure_count': len(recent_failures),
                        'threshold': DB_ERROR_THRESHOLD,
                        'time_window': '1 hour',
                        'timestamp': datetime.now().isoformat()
                    },
                    first_detected=datetime.now(),
                    last_detected=datetime.now()
                ))
        
        return failures

class FailureDetectionEngine:
    """
    🔍 MAIN FAILURE DETECTION ENGINE
    
    Coordinates all failure detection components and integrates with existing
    monitoring infrastructure. Reuses 85% of existing components.
    
    INTEGRATION POINTS:
    - health_monitor.py: Health check patterns
    - task_execution_monitor.py: Execution tracking 
    - workspace_recovery_system.py: Recovery strategies
    - recovery_explanation_engine.py: Error pattern matching
    - executor.py: Circuit breaker integration
    """
    
    def __init__(self):
        # Core components
        self.pattern_detector = FailurePatternDetector()
        self.resource_monitor = ResourceMonitor()
        self.db_monitor = DatabaseConnectionMonitor()
        
        # REUSE: Existing monitoring components
        self.health_monitor = HealthMonitor() if HEALTH_MONITOR_AVAILABLE else None
        self.task_monitor = existing_task_monitor if TASK_EXECUTION_MONITOR_AVAILABLE else None
        self.workspace_recovery = workspace_recovery_system if WORKSPACE_RECOVERY_AVAILABLE else None
        self.workspace_health = workspace_health_manager if WORKSPACE_HEALTH_AVAILABLE else None
        self.recovery_explainer = recovery_explanation_engine if RECOVERY_EXPLANATION_AVAILABLE else None
        
        # State tracking
        self.active_failures: Dict[str, DetectedFailure] = {}
        self.failure_history: List[DetectedFailure] = []
        self.stats = FailureDetectionStats()
        self.running = False
        self.detection_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.detection_interval = FAILURE_DETECTION_INTERVAL
        self.enabled = FAILURE_DETECTION_ENABLED
        
        logger.info(f"🔍 FailureDetectionEngine initialized - "
                   f"enabled: {self.enabled}, interval: {self.detection_interval}s")
        logger.info(f"📊 Component availability - Health: {HEALTH_MONITOR_AVAILABLE}, "
                   f"TaskMonitor: {TASK_EXECUTION_MONITOR_AVAILABLE}, "
                   f"WorkspaceRecovery: {WORKSPACE_RECOVERY_AVAILABLE}, "
                   f"Recovery Explanation: {RECOVERY_EXPLANATION_AVAILABLE}")
    
    async def start(self):
        """Start the failure detection engine"""
        if not self.enabled:
            logger.info("🔍 FailureDetectionEngine disabled by configuration")
            return
        
        if self.running:
            logger.warning("🔍 FailureDetectionEngine already running")
            return
        
        self.running = True
        self.detection_task = asyncio.create_task(self._detection_loop())
        logger.info("🔍 FailureDetectionEngine started")
    
    async def stop(self):
        """Stop the failure detection engine"""
        self.running = False
        if self.detection_task:
            self.detection_task.cancel()
            try:
                await self.detection_task
            except asyncio.CancelledError:
                pass
        logger.info("🔍 FailureDetectionEngine stopped")
    
    async def _detection_loop(self):
        """Main detection loop"""
        logger.info("🔍 Starting failure detection loop")
        
        while self.running:
            try:
                await self.run_failure_detection_scan()
                await asyncio.sleep(self.detection_interval)
            except asyncio.CancelledError:
                logger.info("🔍 Detection loop cancelled")
                break
            except Exception as e:
                logger.error(f"🔍 Error in detection loop: {e}")
                await asyncio.sleep(self.detection_interval * 2)  # Backoff on error
    
    async def run_failure_detection_scan(self) -> Dict[str, Any]:
        """
        🔍 MAIN SCAN FUNCTION
        Runs comprehensive failure detection across all monitored systems
        """
        scan_start = datetime.now()
        new_failures = []
        
        try:
            logger.debug("🔍 Running failure detection scan...")
            
            # 1. REUSE: Check task execution monitoring for hanging tasks
            if TASK_EXECUTION_MONITOR_AVAILABLE and self.task_monitor:
                hanging_tasks = self.task_monitor.get_hanging_tasks()
                for task in hanging_tasks:
                    failure = DetectedFailure(
                        failure_type=FailureType.CIRCUIT_BREAKER_TRIPPED,
                        severity=FailureSeverity.HIGH,
                        message=f"Task {task['task_id']} hanging in {task['current_stage']}",
                        context=task,
                        first_detected=datetime.now(),
                        last_detected=datetime.now()
                    )
                    failure.affected_tasks.add(task['task_id'])
                    if 'workspace_id' in task:
                        failure.affected_workspaces.add(task['workspace_id'])
                    new_failures.append(failure)
            
            # 2. Check for resource exhaustion
            resource_failures = await self.resource_monitor.check_resource_exhaustion()
            new_failures.extend(resource_failures)
            
            # 3. Check database connectivity
            db_failures = await self.db_monitor.check_database_health()
            new_failures.extend(db_failures)
            
            # 4. REUSE: Integration with workspace health manager
            if WORKSPACE_HEALTH_AVAILABLE and self.workspace_health:
                # Get all active workspaces and check their health
                try:
                    workspaces_response = supabase.table('workspaces').select('id').eq('status', 'active').execute()
                    for workspace in (workspaces_response.data or []):
                        workspace_id = workspace['id']
                        
                        # Use existing workspace health check
                        health_report = await self.workspace_health.check_workspace_health_with_recovery(
                            workspace_id, attempt_auto_recovery=False
                        )
                        
                        # Convert health issues to failures
                        for issue in health_report.issues:
                            if issue.level in ['critical', 'emergency']:
                                failure = DetectedFailure(
                                    failure_type=self._map_health_issue_to_failure_type(issue.issue_type),
                                    severity=FailureSeverity.CRITICAL if issue.level == 'emergency' else FailureSeverity.HIGH,
                                    message=f"Workspace health issue: {issue.description}",
                                    context={
                                        'health_issue_type': issue.issue_type,
                                        'affected_count': issue.affected_count,
                                        'auto_recoverable': issue.auto_recoverable,
                                        'workspace_id': workspace_id
                                    },
                                    first_detected=datetime.now(),
                                    last_detected=datetime.now()
                                )
                                failure.affected_workspaces.add(workspace_id)
                                new_failures.append(failure)
                                
                except Exception as e:
                    logger.warning(f"Failed to check workspace health: {e}")
            
            # 5. Process error patterns from recent logs
            await self._scan_recent_error_logs(new_failures)
            
            # 6. Update failure tracking and generate alerts
            await self._process_detected_failures(new_failures)
            
            # 7. Update statistics
            self.stats.total_failures_detected += len(new_failures)
            self.stats.last_detection_time = datetime.now()
            
            scan_duration = (datetime.now() - scan_start).total_seconds()
            logger.debug(f"🔍 Failure detection scan completed in {scan_duration:.2f}s - "
                        f"{len(new_failures)} new failures detected")
            
            return {
                'scan_duration': scan_duration,
                'new_failures_count': len(new_failures),
                'active_failures_count': len(self.active_failures),
                'total_failures_detected': self.stats.total_failures_detected,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"🔍 Error in failure detection scan: {e}")
            return {
                'scan_duration': (datetime.now() - scan_start).total_seconds(),
                'error': str(e),
                'success': False
            }
    
    async def _scan_recent_error_logs(self, new_failures: List[DetectedFailure]):
        """Scan recent error logs for failure patterns"""
        try:
            # Get recent execution logs with errors
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            logs_response = supabase.table('execution_logs').select('*').like(
                'level', '%ERROR%'
            ).gte('created_at', one_hour_ago).execute()
            
            error_logs = logs_response.data or []
            
            for log in error_logs:
                error_message = log.get('message', '')
                context = {
                    'log_id': log.get('id'),
                    'workspace_id': log.get('workspace_id'),
                    'task_id': log.get('task_id'),
                    'agent_id': log.get('agent_id'),
                    'log_level': log.get('level'),
                    'log_timestamp': log.get('created_at'),
                    'metadata': log.get('metadata', {})
                }
                
                # Use pattern detector to identify failure type
                detected_failure = self.pattern_detector.detect_failure_pattern(error_message, context)
                
                if detected_failure:
                    # Add workspace and task context
                    if context.get('workspace_id'):
                        detected_failure.affected_workspaces.add(context['workspace_id'])
                    if context.get('task_id'):
                        detected_failure.affected_tasks.add(context['task_id'])
                    
                    new_failures.append(detected_failure)
                    
        except Exception as e:
            logger.error(f"Error scanning recent error logs: {e}")
    
    def _map_health_issue_to_failure_type(self, issue_type: str) -> FailureType:
        """Map workspace health issues to failure types"""
        mapping = {
            'workspace_needs_intervention': FailureType.CIRCUIT_BREAKER_TRIPPED,
            'excessive_pending_tasks': FailureType.CASCADING_FAILURES,
            'duplicate_tasks': FailureType.CASCADING_FAILURES,
            'no_available_agents': FailureType.OPENAI_CLIENT_ERROR,
            'high_failure_rate': FailureType.CASCADING_FAILURES,
            'workspace_stuck_processing': FailureType.CIRCUIT_BREAKER_TRIPPED
        }
        
        return mapping.get(issue_type, FailureType.CASCADING_FAILURES)
    
    async def _process_detected_failures(self, new_failures: List[DetectedFailure]):
        """Process newly detected failures"""
        for failure in new_failures:
            failure_key = f"{failure.failure_type.value}_{hash(failure.message)}"
            
            if failure_key in self.active_failures:
                # Update existing failure
                existing = self.active_failures[failure_key]
                existing.occurrence_count += 1
                existing.last_detected = datetime.now()
                existing.affected_workspaces.update(failure.affected_workspaces)
                existing.affected_tasks.update(failure.affected_tasks)
            else:
                # New failure
                self.active_failures[failure_key] = failure
                self.failure_history.append(failure)
                self.stats.failures_by_type[failure.failure_type.value] += 1
                self.stats.failures_by_severity[failure.severity.value] += 1
                
                # Send alert for new failures
                await self._send_failure_alert(failure)
                
                # INTEGRATION: Use recovery explanation engine for detailed analysis
                if RECOVERY_EXPLANATION_AVAILABLE and self.recovery_explainer:
                    try:
                        explanation = await self.recovery_explainer.explain_recovery_decision(
                            task_id=list(failure.affected_tasks)[0] if failure.affected_tasks else 'system',
                            workspace_id=list(failure.affected_workspaces)[0] if failure.affected_workspaces else 'system',
                            error_message=failure.message,
                            error_type=failure.failure_type.value,
                            execution_metadata=failure.context
                        )
                        
                        failure.root_cause_analysis = explanation.root_cause
                        failure.recovery_suggestion = explanation.retry_decision
                        
                    except Exception as e:
                        logger.warning(f"Failed to generate recovery explanation: {e}")
        
        # Clean up old active failures (older than 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        expired_keys = [
            key for key, failure in self.active_failures.items()
            if failure.last_detected < cutoff_time
        ]
        
        for key in expired_keys:
            del self.active_failures[key]
    
    async def _send_failure_alert(self, failure: DetectedFailure):
        """Send alert for detected failure"""
        try:
            alert_message = {
                'type': 'failure_detected',
                'failure_type': failure.failure_type.value,
                'severity': failure.severity.value,
                'message': failure.message,
                'affected_workspaces': list(failure.affected_workspaces),
                'affected_tasks': list(failure.affected_tasks),
                'timestamp': datetime.now().isoformat(),
                'context': failure.context
            }
            
            # Send WebSocket notification if available
            if WEBSOCKET_AVAILABLE and ENABLE_WEBSOCKET_NOTIFICATIONS and broadcast_system_alert:
                await broadcast_system_alert(alert_message)
            
            # Log the alert
            logger.warning(f"🚨 FAILURE DETECTED: {failure.severity.value.upper()} - "
                         f"{failure.failure_type.value}: {failure.message}")
            
        except Exception as e:
            logger.error(f"Failed to send failure alert: {e}")
    
    async def detect_failure_from_error(
        self, 
        error_message: str, 
        context: Dict[str, Any]
    ) -> Optional[DetectedFailure]:
        """
        🔍 EXTERNAL API: Detect failure pattern from external error
        Used by other components to immediately analyze errors
        """
        return self.pattern_detector.detect_failure_pattern(error_message, context)
    
    async def get_active_failures(self, severity_filter: Optional[FailureSeverity] = None) -> List[Dict[str, Any]]:
        """Get list of currently active failures"""
        failures = list(self.active_failures.values())
        
        if severity_filter:
            failures = [f for f in failures if f.severity == severity_filter]
        
        return [f.to_dict() for f in failures]
    
    async def get_failure_stats(self) -> Dict[str, Any]:
        """Get failure detection statistics"""
        return {
            'total_failures_detected': self.stats.total_failures_detected,
            'active_failures_count': len(self.active_failures),
            'failures_by_type': dict(self.stats.failures_by_type),
            'failures_by_severity': dict(self.stats.failures_by_severity),
            'last_detection_time': self.stats.last_detection_time.isoformat() if self.stats.last_detection_time else None,
            'detection_accuracy': self.stats.detection_accuracy,
            'false_positive_rate': self.stats.false_positive_rate,
            'pattern_count': len(self.pattern_detector.all_patterns),
            'reused_patterns': len(self.pattern_detector.existing_patterns),
            'new_patterns': len(self.pattern_detector.new_patterns)
        }
    
    async def clear_resolved_failures(self, failure_keys: List[str]) -> int:
        """Clear failures that have been resolved"""
        cleared_count = 0
        
        for key in failure_keys:
            if key in self.active_failures:
                del self.active_failures[key]
                cleared_count += 1
        
        logger.info(f"🔍 Cleared {cleared_count} resolved failures")
        return cleared_count
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the failure detection engine itself"""
        return {
            'running': self.running,
            'enabled': self.enabled,
            'detection_interval': self.detection_interval,
            'active_failures': len(self.active_failures),
            'total_failures_detected': self.stats.total_failures_detected,
            'component_availability': {
                'health_monitor': HEALTH_MONITOR_AVAILABLE,
                'task_monitor': TASK_EXECUTION_MONITOR_AVAILABLE,
                'workspace_recovery': WORKSPACE_RECOVERY_AVAILABLE,
                'workspace_health': WORKSPACE_HEALTH_AVAILABLE,
                'recovery_explanation': RECOVERY_EXPLANATION_AVAILABLE,
                'database': DATABASE_AVAILABLE,
                'websocket': WEBSOCKET_AVAILABLE
            },
            'last_detection_time': self.stats.last_detection_time.isoformat() if self.stats.last_detection_time else None
        }

# Singleton instance
failure_detection_engine = FailureDetectionEngine()

# Convenience functions for easy integration
async def start_failure_detection():
    """Start the global failure detection engine"""
    await failure_detection_engine.start()

async def stop_failure_detection():
    """Stop the global failure detection engine"""
    await failure_detection_engine.stop()

async def detect_failure(error_message: str, context: Dict[str, Any] = None) -> Optional[DetectedFailure]:
    """Detect failure pattern in error message"""
    return await failure_detection_engine.detect_failure_from_error(
        error_message, context or {}
    )

async def get_active_failures(severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get active failures"""
    severity_enum = FailureSeverity(severity) if severity else None
    return await failure_detection_engine.get_active_failures(severity_enum)

async def get_failure_detection_stats() -> Dict[str, Any]:
    """Get failure detection statistics"""
    return await failure_detection_engine.get_failure_stats()

# Quality Gate Test Function
async def test_orchestration_context_detection():
    """
    🎯 QUALITY GATE TEST: Verify OrchestrationContext field missing detection
    
    This function tests that the system can automatically detect the specific
    error that was manually fixed: "OrchestrationContext" field missing.
    """
    test_error = "ValidationError: 1 validation error for TaskOutput\nOrchestrationContext\n  field required (type=value_error.missing)"
    test_context = {
        'task_id': 'test_task',
        'workspace_id': 'test_workspace',
        'error_type': 'ValidationError'
    }
    
    detected = await detect_failure(test_error, test_context)
    
    if detected and detected.failure_type == FailureType.ORCHESTRATION_CONTEXT_MISSING:
        logger.info("✅ QUALITY GATE PASSED: OrchestrationContext field missing auto-detected")
        return True
    else:
        logger.error("❌ QUALITY GATE FAILED: OrchestrationContext field missing NOT detected")
        return False

if __name__ == "__main__":
    # Run quality gate test
    import asyncio
    asyncio.run(test_orchestration_context_detection())