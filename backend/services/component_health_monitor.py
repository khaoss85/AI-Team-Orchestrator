"""
Component Health Monitor - Sistema di monitoraggio salute componenti

Implementa heartbeat automatico e monitoring per tutti i componenti del sistema.
Integrato con orchestration_flows per tracking end-to-end.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Livelli di salute dei componenti"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
    UNKNOWN = "unknown"

@dataclass
class HealthMetrics:
    """Metriche di salute di un componente"""
    response_time_ms: float
    error_rate: float
    throughput_per_minute: float
    memory_usage_mb: float
    last_error: Optional[str] = None
    custom_metrics: Dict[str, Any] = None

class ComponentHealthMonitor:
    """
    Sistema di monitoraggio salute componenti con heartbeat automatico
    """
    
    def __init__(self):
        self.supabase = None
        self._initialize_database()
        
        # Configurazione monitoring
        self.heartbeat_interval = 30  # secondi
        self.health_check_interval = 60  # secondi
        self.failure_threshold = 3  # tentativi falliti prima di marcare unhealthy
        
        # Stato monitoring
        self._monitoring_active = False
        self._component_metrics: Dict[str, HealthMetrics] = {}
        self._last_health_check = {}
        
        # Componenti registrati per monitoraggio
        self.monitored_components = {
            'unified_orchestrator': {
                'check_method': self._check_unified_orchestrator,
                'critical': True
            },
            'deliverable_pipeline': {
                'check_method': self._check_deliverable_pipeline,
                'critical': True
            },
            'executor': {
                'check_method': self._check_executor,
                'critical': True
            },
            'quality_gate': {
                'check_method': self._check_quality_gate,
                'critical': True
            },
            'memory_system': {
                'check_method': self._check_memory_system,
                'critical': True
            },
            'automatic_quality_trigger': {
                'check_method': self._check_quality_trigger,
                'critical': False
            },
            'asset_requirements_generator': {
                'check_method': self._check_asset_generator,
                'critical': False
            }
        }
        
        logger.info("🏥 ComponentHealthMonitor initialized")
    
    def _initialize_database(self):
        """Inizializza connessione database"""
        try:
            from database import get_supabase_client
            self.supabase = get_supabase_client()
            logger.info("✅ Database connection initialized for health monitoring")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database for health monitoring: {e}")
    
    async def start_monitoring(self):
        """Avvia il sistema di monitoraggio"""
        self._monitoring_active = True
        logger.info("🚀 Starting component health monitoring system")
        
        # Avvia tasks di monitoraggio in parallelo
        monitoring_tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        try:
            await asyncio.gather(*monitoring_tasks)
        except Exception as e:
            logger.error(f"Health monitoring system error: {e}")
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Ferma il sistema di monitoraggio"""
        self._monitoring_active = False
        logger.info("🛑 Component health monitoring stopped")
    
    async def _heartbeat_loop(self):
        """Loop principale per heartbeat dei componenti"""
        while self._monitoring_active:
            try:
                await self._send_heartbeats()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)
    
    async def _health_check_loop(self):
        """Loop per controlli di salute dettagliati"""
        while self._monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_loop(self):
        """Loop per pulizia dati vecchi e manutenzione"""
        while self._monitoring_active:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(300)  # ogni 5 minuti
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _send_heartbeats(self):
        """Invia heartbeat per tutti i componenti monitorati"""
        try:
            current_time = datetime.now(timezone.utc)
            
            for component_name, config in self.monitored_components.items():
                try:
                    # Verifica se il componente è disponibile
                    is_available = await self._check_component_availability(component_name)
                    
                    # Aggiorna heartbeat nel database
                    await self._update_heartbeat(component_name, is_available, current_time)
                    
                except Exception as e:
                    logger.error(f"Failed to send heartbeat for {component_name}: {e}")
                    await self._update_heartbeat(component_name, False, current_time, str(e))
            
            logger.debug(f"✅ Heartbeats sent for {len(self.monitored_components)} components")
            
        except Exception as e:
            logger.error(f"Failed to send heartbeats: {e}")
    
    async def _perform_health_checks(self):
        """Esegue controlli di salute dettagliati"""
        try:
            for component_name, config in self.monitored_components.items():
                try:
                    # Esegui check specifico del componente
                    health_metrics = await config['check_method']()
                    
                    # Calcola stato di salute
                    health_status = self._calculate_health_status(health_metrics)
                    
                    # Aggiorna database con metriche dettagliate
                    await self._update_component_health(component_name, health_status, health_metrics)
                    
                    self._component_metrics[component_name] = health_metrics
                    self._last_health_check[component_name] = datetime.now()
                    
                except Exception as e:
                    logger.error(f"Health check failed for {component_name}: {e}")
                    unhealthy_metrics = HealthMetrics(
                        response_time_ms=float('inf'),
                        error_rate=1.0,
                        throughput_per_minute=0.0,
                        memory_usage_mb=0.0,
                        last_error=str(e)
                    )
                    await self._update_component_health(component_name, HealthStatus.UNHEALTHY, unhealthy_metrics)
            
            logger.debug(f"✅ Health checks completed for {len(self.monitored_components)} components")
            
        except Exception as e:
            logger.error(f"Failed to perform health checks: {e}")
    
    async def _check_component_availability(self, component_name: str) -> bool:
        """Verifica disponibilità base di un componente"""
        try:
            if component_name == 'unified_orchestrator':
                from unified_orchestrator import unified_orchestrator
                return hasattr(unified_orchestrator, 'start')
            
            elif component_name == 'deliverable_pipeline':
                from deliverable_system.deliverable_pipeline import deliverable_pipeline
                return hasattr(deliverable_pipeline, 'start')
            
            elif component_name == 'executor':
                import executor
                return hasattr(executor, 'start_task_executor')
            
            elif component_name == 'quality_gate':
                from quality_gate import QualityGate
                return True
            
            elif component_name == 'memory_system':
                from services.memory_system import memory_system
                return hasattr(memory_system, 'store_context')
            
            elif component_name == 'automatic_quality_trigger':
                from services.automatic_quality_trigger import get_automatic_quality_trigger
                return True
            
            elif component_name == 'asset_requirements_generator':
                from services.asset_requirements_generator import AssetRequirementsGenerator
                return True
            
            return False
            
        except ImportError:
            return False
        except Exception as e:
            logger.debug(f"Component {component_name} availability check failed: {e}")
            return False
    
    # Metodi di check specifici per ogni componente
    async def _check_unified_orchestrator(self) -> HealthMetrics:
        """Check salute unified orchestrator"""
        start_time = time.time()
        try:
            from unified_orchestrator import unified_orchestrator
            
            # Verifica che l'orchestrator sia disponibile
            if hasattr(unified_orchestrator, '_active_flows'):
                active_flows = len(unified_orchestrator._active_flows)
                response_time = (time.time() - start_time) * 1000
                
                return HealthMetrics(
                    response_time_ms=response_time,
                    error_rate=0.0,
                    throughput_per_minute=active_flows * 2,  # stima
                    memory_usage_mb=50.0,  # stima
                    custom_metrics={"active_flows": active_flows}
                )
            else:
                return HealthMetrics(
                    response_time_ms=float('inf'),
                    error_rate=1.0,
                    throughput_per_minute=0.0,
                    memory_usage_mb=0.0,
                    last_error="Orchestrator not properly initialized"
                )
                
        except Exception as e:
            return HealthMetrics(
                response_time_ms=float('inf'),
                error_rate=1.0,
                throughput_per_minute=0.0,
                memory_usage_mb=0.0,
                last_error=str(e)
            )
    
    async def _check_deliverable_pipeline(self) -> HealthMetrics:
        """Check salute deliverable pipeline"""
        start_time = time.time()
        try:
            from deliverable_system.deliverable_pipeline import deliverable_pipeline
            
            # Verifica stato pipeline
            if hasattr(deliverable_pipeline, '_running'):
                is_running = deliverable_pipeline._running
                response_time = (time.time() - start_time) * 1000
                
                return HealthMetrics(
                    response_time_ms=response_time,
                    error_rate=0.0 if is_running else 0.5,
                    throughput_per_minute=10.0 if is_running else 0.0,
                    memory_usage_mb=30.0,
                    custom_metrics={"is_running": is_running}
                )
            else:
                return HealthMetrics(
                    response_time_ms=float('inf'),
                    error_rate=1.0,
                    throughput_per_minute=0.0,
                    memory_usage_mb=0.0,
                    last_error="Pipeline not initialized"
                )
                
        except Exception as e:
            return HealthMetrics(
                response_time_ms=float('inf'),
                error_rate=1.0,
                throughput_per_minute=0.0,
                memory_usage_mb=0.0,
                last_error=str(e)
            )
    
    async def _check_executor(self) -> HealthMetrics:
        """Check salute executor"""
        start_time = time.time()
        try:
            # Verifica che l'executor sia importabile
            import executor
            response_time = (time.time() - start_time) * 1000
            
            return HealthMetrics(
                response_time_ms=response_time,
                error_rate=0.0,
                throughput_per_minute=15.0,
                memory_usage_mb=100.0,
                custom_metrics={"module_loaded": True}
            )
            
        except Exception as e:
            return HealthMetrics(
                response_time_ms=float('inf'),
                error_rate=1.0,
                throughput_per_minute=0.0,
                memory_usage_mb=0.0,
                last_error=str(e)
            )
    
    async def _check_quality_gate(self) -> HealthMetrics:
        """Check salute quality gate"""
        start_time = time.time()
        try:
            from quality_gate import QualityGate
            gate = QualityGate()
            response_time = (time.time() - start_time) * 1000
            
            return HealthMetrics(
                response_time_ms=response_time,
                error_rate=0.0,
                throughput_per_minute=8.0,
                memory_usage_mb=25.0,
                custom_metrics={"quality_gate_ready": True}
            )
            
        except Exception as e:
            return HealthMetrics(
                response_time_ms=float('inf'),
                error_rate=1.0,
                throughput_per_minute=0.0,
                memory_usage_mb=0.0,
                last_error=str(e)
            )
    
    async def _check_memory_system(self) -> HealthMetrics:
        """Check salute memory system"""
        start_time = time.time()
        try:
            from services.memory_system import memory_system
            
            # Test basic functionality
            if hasattr(memory_system, 'supabase'):
                response_time = (time.time() - start_time) * 1000
                
                return HealthMetrics(
                    response_time_ms=response_time,
                    error_rate=0.0,
                    throughput_per_minute=12.0,
                    memory_usage_mb=40.0,
                    custom_metrics={"memory_system_ready": True}
                )
            else:
                return HealthMetrics(
                    response_time_ms=float('inf'),
                    error_rate=1.0,
                    throughput_per_minute=0.0,
                    memory_usage_mb=0.0,
                    last_error="Memory system not properly initialized"
                )
                
        except Exception as e:
            return HealthMetrics(
                response_time_ms=float('inf'),
                error_rate=1.0,
                throughput_per_minute=0.0,
                memory_usage_mb=0.0,
                last_error=str(e)
            )
    
    async def _check_quality_trigger(self) -> HealthMetrics:
        """Check salute quality trigger"""
        start_time = time.time()
        try:
            from services.automatic_quality_trigger import get_automatic_quality_trigger
            trigger = get_automatic_quality_trigger()
            response_time = (time.time() - start_time) * 1000
            
            return HealthMetrics(
                response_time_ms=response_time,
                error_rate=0.0,
                throughput_per_minute=5.0,
                memory_usage_mb=20.0,
                custom_metrics={"trigger_ready": True}
            )
            
        except Exception as e:
            return HealthMetrics(
                response_time_ms=float('inf'),
                error_rate=1.0,
                throughput_per_minute=0.0,
                memory_usage_mb=0.0,
                last_error=str(e)
            )
    
    async def _check_asset_generator(self) -> HealthMetrics:
        """Check salute asset generator"""
        start_time = time.time()
        try:
            from services.asset_requirements_generator import AssetRequirementsGenerator
            generator = AssetRequirementsGenerator()
            response_time = (time.time() - start_time) * 1000
            
            return HealthMetrics(
                response_time_ms=response_time,
                error_rate=0.0,
                throughput_per_minute=6.0,
                memory_usage_mb=35.0,
                custom_metrics={"generator_ready": True}
            )
            
        except Exception as e:
            return HealthMetrics(
                response_time_ms=float('inf'),
                error_rate=1.0,
                throughput_per_minute=0.0,
                memory_usage_mb=0.0,
                last_error=str(e)
            )
    
    def _calculate_health_status(self, metrics: HealthMetrics) -> HealthStatus:
        """Calcola stato di salute basato su metriche"""
        try:
            # Calcola score complessivo
            score = 1.0
            
            # Penalizza tempi di risposta alti
            if metrics.response_time_ms > 5000:  # > 5 secondi
                score -= 0.4
            elif metrics.response_time_ms > 1000:  # > 1 secondo
                score -= 0.2
            
            # Penalizza alto error rate
            score -= metrics.error_rate * 0.5
            
            # Penalizza basso throughput (se esperato > 0)
            if metrics.throughput_per_minute == 0:
                score -= 0.3
            
            # Controlla se ci sono errori recenti
            if metrics.last_error:
                score -= 0.2
            
            # Determina status finale
            if score >= 0.8:
                return HealthStatus.HEALTHY
            elif score >= 0.5:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.UNHEALTHY
                
        except Exception as e:
            logger.error(f"Error calculating health status: {e}")
            return HealthStatus.UNKNOWN
    
    async def _update_heartbeat(self, component_name: str, is_available: bool, 
                              timestamp: datetime, error: str = None):
        """Aggiorna heartbeat nel database"""
        try:
            if not self.supabase:
                return
            
            health_data = {
                'last_heartbeat': timestamp.isoformat(),
                'status': 'healthy' if is_available else 'unhealthy',
                'updated_at': timestamp.isoformat(),
                'component_type': 'CORE' if self.monitored_components.get(component_name, {}).get('critical') else 'SUPPORT'
            }
            
            if error:
                health_data['last_error'] = error
                health_data['consecutive_failures'] = self.supabase.table('component_health').select('consecutive_failures').eq('component_name', component_name).execute()
                current_failures = health_data.get('consecutive_failures', 0) if health_data else 0
                health_data['consecutive_failures'] = current_failures + 1
            else:
                health_data['consecutive_failures'] = 0
                health_data['last_success_at'] = timestamp.isoformat()
            
            self.supabase.table('component_health').upsert(
                {**health_data, 'component_name': component_name},
                on_conflict='component_name'
            ).execute()
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat for {component_name}: {e}")
    
    async def _update_component_health(self, component_name: str, status: HealthStatus, 
                                     metrics: HealthMetrics):
        """Aggiorna salute completa del componente"""
        try:
            if not self.supabase:
                return
            
            health_score = 1.0 - metrics.error_rate if metrics.error_rate <= 1.0 else 0.0
            
            health_data = {
                'component_name': component_name,
                'status': status.value,
                'health_score': health_score,
                'avg_response_time_ms': metrics.response_time_ms if metrics.response_time_ms != float('inf') else None,
                'error_rate': metrics.error_rate,
                'throughput_per_minute': metrics.throughput_per_minute,
                'last_error': metrics.last_error,
                'component_type': 'CORE' if self.monitored_components.get(component_name, {}).get('critical') else 'SUPPORT',
                'metadata': {
                    'memory_usage_mb': metrics.memory_usage_mb,
                    'custom_metrics': metrics.custom_metrics or {},
                    'last_health_check': datetime.now(timezone.utc).isoformat()
                },
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table('component_health').upsert(
                health_data,
                on_conflict='component_name'
            ).execute()
            
            logger.debug(f"Updated health for {component_name}: {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update component health for {component_name}: {e}")
    
    async def _cleanup_old_data(self):
        """Pulisce dati vecchi e ottimizza database"""
        try:
            if not self.supabase:
                return
            
            # Cleanup eventi vecchi (più di 7 giorni)
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            
            self.supabase.table('integration_events').delete().lt('created_at', cutoff_date).eq('status', 'completed').execute()
            
            logger.debug("✅ Cleanup completed for old integration events")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Ottieni riassunto salute sistema"""
        try:
            if not self.supabase:
                return {"error": "Database not available"}
            
            # Get current health status
            result = self.supabase.table('component_health').select('*').execute()
            
            if not result.data:
                return {"error": "No health data available"}
            
            components = result.data
            total_components = len(components)
            healthy_count = sum(1 for c in components if c['status'] == 'healthy')
            degraded_count = sum(1 for c in components if c['status'] == 'degraded')
            unhealthy_count = sum(1 for c in components if c['status'] == 'unhealthy')
            
            overall_health = "healthy" if unhealthy_count == 0 and degraded_count <= 1 else \
                           "degraded" if unhealthy_count <= 1 else "unhealthy"
            
            return {
                "overall_health": overall_health,
                "total_components": total_components,
                "healthy_components": healthy_count,
                "degraded_components": degraded_count,
                "unhealthy_components": unhealthy_count,
                "components": components,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health summary: {e}")
            return {"error": str(e)}


# Global instance
component_health_monitor = ComponentHealthMonitor()

# Convenience functions
async def start_health_monitoring():
    """Avvia monitoraggio salute componenti"""
    await component_health_monitor.start_monitoring()

async def stop_health_monitoring():
    """Ferma monitoraggio salute componenti"""
    await component_health_monitor.stop_monitoring()

async def get_system_health():
    """Ottieni stato salute sistema"""
    return await component_health_monitor.get_system_health_summary()

if __name__ == "__main__":
    # Test del sistema di monitoraggio
    async def test_health_monitor():
        print("🏥 Testing Component Health Monitor")
        print("=" * 50)
        
        monitor = ComponentHealthMonitor()
        
        # Test health summary
        summary = await monitor.get_system_health_summary()
        print(f"System Health: {summary}")
    
    asyncio.run(test_health_monitor())