#!/usr/bin/env python3
"""
🔍 TASK EXECUTION MONITOR - Diagnostica Avanzata
================================================================================
Sistema di monitoring per identificare dove i task si bloccano durante l'esecuzione.

Questo modulo fornisce:
1. Heartbeat monitoring per task execution
2. Performance timing per ogni fase
3. Deadlock detection 
4. Error pattern analysis
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ExecutionStage(Enum):
    """Stages del task execution per tracking dettagliato"""
    TASK_RECEIVED = "task_received"
    AGENT_ASSIGNED = "agent_assigned"
    AGENT_INITIALIZED = "agent_initialized"
    SDK_SESSION_CREATED = "sdk_session_created"
    RUNNER_START = "runner_start"
    RUNNER_EXECUTING = "runner_executing"
    RUNNER_COMPLETED = "runner_completed"
    JSON_PARSING = "json_parsing"
    RESULT_VALIDATION = "result_validation"
    DB_UPDATE_START = "db_update_start"
    DB_UPDATE_COMPLETED = "db_update_completed"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

@dataclass
class TaskExecutionTrace:
    """Tracciamento completo dell'esecuzione di un task"""
    task_id: str
    workspace_id: str
    agent_id: Optional[str]
    start_time: datetime
    current_stage: ExecutionStage
    stage_history: List[tuple[ExecutionStage, datetime, Optional[str]]]  # stage, timestamp, note
    is_hanging: bool = False
    hang_detection_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class TaskExecutionMonitor:
    """
    🕵️ Sistema di monitoring per task execution
    
    Monitora ogni fase dell'esecuzione dei task per identificare
    punti di blocco, performance issues e pattern di errore.
    """
    
    def __init__(self, hang_detection_threshold: int = 180):  # 3 minuti
        self.traces: Dict[str, TaskExecutionTrace] = {}
        self.hang_detection_threshold = hang_detection_threshold
        self.monitoring_active = True
        
    async def start_monitoring(self):
        """Avvia il monitoring in background"""
        logger.info("🔍 Task Execution Monitor started")
        asyncio.create_task(self._background_monitor())
    
    def trace_task_start(self, task_id: str, workspace_id: str, agent_id: Optional[str] = None) -> TaskExecutionTrace:
        """Inizia il tracking di un task"""
        trace = TaskExecutionTrace(
            task_id=task_id,
            workspace_id=workspace_id,
            agent_id=agent_id,
            start_time=datetime.now(),
            current_stage=ExecutionStage.TASK_RECEIVED,
            stage_history=[(ExecutionStage.TASK_RECEIVED, datetime.now(), None)]
        )
        self.traces[task_id] = trace
        logger.info(f"📝 Started tracking task {task_id}")
        return trace
    
    def trace_stage(self, task_id: str, stage: ExecutionStage, note: Optional[str] = None):
        """Registra il passaggio a una nuova fase dell'esecuzione"""
        if task_id not in self.traces:
            logger.warning(f"⚠️ Cannot trace stage {stage} for unknown task {task_id}")
            return
            
        trace = self.traces[task_id]
        now = datetime.now()
        
        # Calcola tempo speso nella fase precedente
        if trace.stage_history:
            prev_stage, prev_time, _ = trace.stage_history[-1]
            phase_duration = (now - prev_time).total_seconds()
            logger.debug(f"⏱️ Task {task_id}: {prev_stage.value} → {stage.value} ({phase_duration:.2f}s)")
        
        trace.current_stage = stage
        trace.stage_history.append((stage, now, note))
        
        # Reset hang detection se il task sta progredendo
        if trace.is_hanging:
            trace.is_hanging = False
            trace.hang_detection_time = None
            logger.info(f"✅ Task {task_id} resumed from hanging state")
    
    def trace_error(self, task_id: str, error: str, stage: Optional[ExecutionStage] = None):
        """Registra un errore durante l'esecuzione"""
        if task_id not in self.traces:
            logger.warning(f"⚠️ Cannot trace error for unknown task {task_id}")
            return
            
        trace = self.traces[task_id]
        trace.errors.append(f"{datetime.now().isoformat()}: {error}")
        
        if stage:
            self.trace_stage(task_id, stage, f"ERROR: {error}")
        
        logger.error(f"❌ Task {task_id} error in {trace.current_stage.value}: {error}")
    
    def trace_task_complete(self, task_id: str, success: bool = True):
        """Completa il tracking di un task"""
        if task_id not in self.traces:
            logger.warning(f"⚠️ Cannot complete trace for unknown task {task_id}")
            return
            
        trace = self.traces[task_id]
        final_stage = ExecutionStage.TASK_COMPLETED if success else ExecutionStage.TASK_FAILED
        self.trace_stage(task_id, final_stage)
        
        trace.total_execution_time = (datetime.now() - trace.start_time).total_seconds()
        
        # Log summary
        logger.info(f"📊 Task {task_id} {'completed' if success else 'failed'} "
                   f"in {trace.total_execution_time:.2f}s "
                   f"({len(trace.stage_history)} stages, {len(trace.errors)} errors)")
        
        # Rimuovi dalla tracking attiva dopo un delay
        asyncio.create_task(self._cleanup_trace(task_id, delay=300))  # 5 minuti
    
    async def _cleanup_trace(self, task_id: str, delay: int = 300):
        """Rimuove trace vecchie per non saturare memoria"""
        await asyncio.sleep(delay)
        if task_id in self.traces:
            del self.traces[task_id]
            logger.debug(f"🧹 Cleaned up trace for task {task_id}")
    
    async def _background_monitor(self):
        """Monitoring in background per hang detection"""
        while self.monitoring_active:
            await asyncio.sleep(30)  # Check ogni 30 secondi
            await self._check_hanging_tasks()
    
    async def _check_hanging_tasks(self):
        """Identifica task che potrebbero essere bloccati"""
        now = datetime.now()
        hanging_tasks = []
        
        for task_id, trace in self.traces.items():
            # Skip task già completati
            if trace.current_stage in [ExecutionStage.TASK_COMPLETED, ExecutionStage.TASK_FAILED]:
                continue
                
            # Calcola tempo nella fase corrente
            if trace.stage_history:
                _, last_update, _ = trace.stage_history[-1]
                time_in_current_stage = (now - last_update).total_seconds()
                
                if time_in_current_stage > self.hang_detection_threshold:
                    if not trace.is_hanging:
                        trace.is_hanging = True
                        trace.hang_detection_time = now
                        hanging_tasks.append((task_id, trace))
                        
                        logger.warning(f"🚨 HANG DETECTED: Task {task_id} stuck in {trace.current_stage.value} "
                                      f"for {time_in_current_stage:.0f}s (threshold: {self.hang_detection_threshold}s)")
        
        if hanging_tasks:
            await self._analyze_hanging_patterns(hanging_tasks)
    
    async def _analyze_hanging_patterns(self, hanging_tasks: List[tuple[str, TaskExecutionTrace]]):
        """Analizza pattern comuni nei task bloccati"""
        hanging_stages = {}
        
        for task_id, trace in hanging_tasks:
            stage = trace.current_stage.value
            if stage not in hanging_stages:
                hanging_stages[stage] = []
            hanging_stages[stage].append(task_id)
        
        for stage, tasks in hanging_stages.items():
            logger.error(f"🔥 PATTERN DETECTED: {len(tasks)} tasks hanging in {stage}: {tasks}")
    
    def get_trace_summary(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Ottiene summary del trace per un task"""
        if task_id not in self.traces:
            return None
            
        trace = self.traces[task_id]
        return {
            "task_id": task_id,
            "workspace_id": trace.workspace_id,
            "agent_id": trace.agent_id,
            "current_stage": trace.current_stage.value,
            "execution_time": (datetime.now() - trace.start_time).total_seconds(),
            "is_hanging": trace.is_hanging,
            "stage_count": len(trace.stage_history),
            "error_count": len(trace.errors),
            "stages": [
                {
                    "stage": stage.value,
                    "timestamp": timestamp.isoformat(),
                    "note": note
                }
                for stage, timestamp, note in trace.stage_history
            ],
            "errors": trace.errors
        }
    
    def get_all_active_traces(self) -> Dict[str, Dict[str, Any]]:
        """Ottiene tutti i trace attivi"""
        return {
            task_id: self.get_trace_summary(task_id)
            for task_id in self.traces.keys()
        }
    
    def get_hanging_tasks(self) -> List[Dict[str, Any]]:
        """Ottiene lista dei task attualmente bloccati"""
        return [
            self.get_trace_summary(task_id)
            for task_id, trace in self.traces.items()
            if trace.is_hanging
        ]

# Singleton instance
task_monitor = TaskExecutionMonitor()

# Convenience functions
async def start_monitoring():
    """Avvia il monitoring globale"""
    await task_monitor.start_monitoring()

def trace_task_start(task_id: str, workspace_id: str, agent_id: Optional[str] = None):
    """Wrapper per trace_task_start"""
    return task_monitor.trace_task_start(task_id, workspace_id, agent_id)

def trace_stage(task_id: str, stage: ExecutionStage, note: Optional[str] = None):
    """Wrapper per trace_stage"""
    task_monitor.trace_stage(task_id, stage, note)

def trace_error(task_id: str, error: str, stage: Optional[ExecutionStage] = None):
    """Wrapper per trace_error"""
    task_monitor.trace_error(task_id, error, stage)

def trace_task_complete(task_id: str, success: bool = True):
    """Wrapper per trace_task_complete"""
    task_monitor.trace_task_complete(task_id, success)