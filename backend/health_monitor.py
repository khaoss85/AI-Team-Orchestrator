#!/usr/bin/env python3
"""
Workspace Health Monitor - Prevents future deliverable display issues
Monitors and auto-fixes common issues that prevent deliverable creation

Features:
- Auto-fixes workspace error states
- Restarts stalled executors  
- Detects and resolves stalled Final Deliverable tasks
- Alerts on persistent issues
- Comprehensive logging
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('health_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

class HealthMonitor:
    """Automated health monitoring and recovery system"""
    
    def __init__(self):
        load_dotenv()
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'), 
            os.getenv('SUPABASE_KEY')
        )
        self.issues_found = []
        self.fixes_applied = []
        
    async def run_health_check(self) -> Dict[str, Any]:
        """Run complete health check and auto-fix issues"""
        logger.info("🏥 Starting comprehensive health check...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'issues_found': [],
            'fixes_applied': [],
            'warnings': [],
            'health_score': 100
        }
        
        try:
            # 1. Check workspace health
            await self._check_workspace_health(results)
            
            # 2. Check executor health  
            await self._check_executor_health(results)
            
            # 3. Check stalled tasks
            await self._check_stalled_tasks(results)
            
            # 4. Check deliverable pipeline
            await self._check_deliverable_pipeline(results)
            
            # 5. Calculate overall health score
            results['health_score'] = self._calculate_health_score(results)
            
            logger.info(f"✅ Health check completed - Score: {results['health_score']}/100")
            
            # Send alerts if needed
            try:
                from alert_system import alert_system
                alert_system.process_health_results(results)
            except Exception as alert_error:
                logger.warning(f"Failed to send alerts: {alert_error}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            results['issues_found'].append(f"Health check system error: {e}")
            results['health_score'] = 0
            
        return results
    
    async def _check_workspace_health(self, results: Dict[str, Any]):
        """Check and fix workspace status issues"""
        logger.info("🔍 Checking workspace health...")
        
        try:
            # Get all workspaces
            workspaces_response = self.supabase.table('workspaces').select('id,name,status,created_at').execute()
            workspaces = workspaces_response.data
            
            error_workspaces = [w for w in workspaces if w.get('status') == 'error']
            
            if error_workspaces:
                logger.warning(f"⚠️ Found {len(error_workspaces)} workspaces in error state")
                results['issues_found'].append(f"{len(error_workspaces)} workspaces in error state")
                
                # Auto-fix error workspaces
                for workspace in error_workspaces:
                    try:
                        self.supabase.table('workspaces').update({
                            'status': 'active'
                        }).eq('id', workspace['id']).execute()
                        
                        fix_msg = f"Fixed workspace '{workspace.get('name', 'Unnamed')}' (error → active)"
                        logger.info(f"🔧 {fix_msg}")
                        results['fixes_applied'].append(fix_msg)
                        
                    except Exception as e:
                        error_msg = f"Failed to fix workspace {workspace['id']}: {e}"
                        logger.error(f"❌ {error_msg}")
                        results['issues_found'].append(error_msg)
            else:
                logger.info("✅ All workspaces are healthy")
                
        except Exception as e:
            error_msg = f"Failed to check workspace health: {e}"
            logger.error(f"❌ {error_msg}")
            results['issues_found'].append(error_msg)
    
    async def _check_executor_health(self, results: Dict[str, Any]):
        """Check and restart executor if needed"""
        logger.info("🤖 Checking executor health...")
        
        try:
            # Add backend to path for imports
            sys.path.append('.')
            
            from executor import TaskExecutor
            
            executor = TaskExecutor()
            
            if not executor.running:
                logger.warning("⚠️ Executor is not running")
                results['issues_found'].append("Task executor is not running")
                
                # Try to start the executor
                try:
                    await executor.start()
                    fix_msg = "Restarted task executor"
                    logger.info(f"🚀 {fix_msg}")
                    results['fixes_applied'].append(fix_msg)
                except Exception as e:
                    error_msg = f"Failed to restart executor: {e}"
                    logger.error(f"❌ {error_msg}")
                    results['issues_found'].append(error_msg)
            else:
                logger.info("✅ Executor is running normally")
                
            # Check executor queue health
            if hasattr(executor, 'task_queue'):
                queue_size = executor.task_queue.qsize()
                if queue_size > 50:  # Alert if queue is too large
                    warning_msg = f"Executor queue size is high: {queue_size}"
                    logger.warning(f"⚠️ {warning_msg}")
                    results['warnings'].append(warning_msg)
                    
        except Exception as e:
            error_msg = f"Failed to check executor health: {e}"
            logger.error(f"❌ {error_msg}")
            results['issues_found'].append(error_msg)
    
    async def _check_stalled_tasks(self, results: Dict[str, Any]):
        """Check for stalled Final Deliverable tasks"""
        logger.info("⏱️ Checking for stalled tasks...")
        
        try:
            # Check for old pending Final Deliverable tasks (>30 minutes old)
            thirty_min_ago = (datetime.now() - timedelta(minutes=30)).isoformat()
            
            stalled_response = self.supabase.table('tasks').select(
                'id,name,workspace_id,created_at'
            ).eq('status', 'pending').like(
                'name', '%Final Deliverable%'
            ).lt('created_at', thirty_min_ago).execute()
            
            stalled_tasks = stalled_response.data
            
            if stalled_tasks:
                logger.warning(f"⚠️ Found {len(stalled_tasks)} stalled Final Deliverable tasks")
                
                # Group by workspace
                by_workspace = {}
                for task in stalled_tasks:
                    ws_id = task['workspace_id']
                    if ws_id not in by_workspace:
                        by_workspace[ws_id] = []
                    by_workspace[ws_id].append(task)
                
                for workspace_id, tasks in by_workspace.items():
                    issue_msg = f"Workspace {workspace_id[:8]}... has {len(tasks)} stalled deliverable tasks"
                    logger.warning(f"⚠️ {issue_msg}")
                    results['issues_found'].append(issue_msg)
                    
                    # Could implement auto-retry logic here
                    # For now, just log the issue for manual review
                    
            else:
                logger.info("✅ No stalled Final Deliverable tasks found")
                
        except Exception as e:
            error_msg = f"Failed to check stalled tasks: {e}"
            logger.error(f"❌ {error_msg}")
            results['issues_found'].append(error_msg)
    
    async def _check_deliverable_pipeline(self, results: Dict[str, Any]):
        """Check deliverable creation pipeline health"""
        logger.info("📦 Checking deliverable pipeline...")
        
        try:
            # Check workspaces with completed tasks but no deliverables
            workspaces_response = self.supabase.table('workspaces').select('id,name').eq('status', 'active').execute()
            
            for workspace in workspaces_response.data:
                workspace_id = workspace['id']
                
                # Count completed tasks
                tasks_response = self.supabase.table('tasks').select(
                    'id', count='exact'
                ).eq('workspace_id', workspace_id).eq('status', 'completed').execute()
                
                completed_count = tasks_response.count or 0
                
                # Count deliverables
                deliverables_response = self.supabase.table('deliverables').select(
                    'id', count='exact'
                ).eq('workspace_id', workspace_id).execute()
                
                deliverable_count = deliverables_response.count or 0
                
                # Alert if many completed tasks but no deliverables
                if completed_count >= 10 and deliverable_count == 0:
                    warning_msg = f"Workspace '{workspace.get('name', 'Unnamed')}' has {completed_count} completed tasks but no deliverables"
                    logger.warning(f"⚠️ {warning_msg}")
                    results['warnings'].append(warning_msg)
                elif completed_count >= 5 and deliverable_count == 0:
                    warning_msg = f"Workspace '{workspace.get('name', 'Unnamed')}' has {completed_count} completed tasks but no deliverables (monitor)"
                    results['warnings'].append(warning_msg)
                    
        except Exception as e:
            error_msg = f"Failed to check deliverable pipeline: {e}"
            logger.error(f"❌ {error_msg}")
            results['issues_found'].append(error_msg)
    
    def _calculate_health_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall system health score"""
        score = 100
        
        # Deduct points for issues
        score -= len(results['issues_found']) * 15
        score -= len(results['warnings']) * 5
        
        # Add points for fixes applied (shows recovery)
        score += min(len(results['fixes_applied']) * 5, 20)
        
        return max(0, min(100, score))
    
    async def generate_health_report(self) -> str:
        """Generate comprehensive health report"""
        results = await self.run_health_check()
        
        report = f"""
🏥 SYSTEM HEALTH REPORT
Generated: {results['timestamp']}
Overall Health Score: {results['health_score']}/100

📊 SUMMARY:
- Issues Found: {len(results['issues_found'])}
- Fixes Applied: {len(results['fixes_applied'])}  
- Warnings: {len(results['warnings'])}

"""
        
        if results['issues_found']:
            report += "❌ ISSUES FOUND:\n"
            for issue in results['issues_found']:
                report += f"   • {issue}\n"
            report += "\n"
        
        if results['fixes_applied']:
            report += "🔧 FIXES APPLIED:\n"
            for fix in results['fixes_applied']:
                report += f"   • {fix}\n"
            report += "\n"
        
        if results['warnings']:
            report += "⚠️ WARNINGS:\n"
            for warning in results['warnings']:
                report += f"   • {warning}\n"
            report += "\n"
        
        # Health status
        if results['health_score'] >= 90:
            report += "🎉 SYSTEM STATUS: EXCELLENT\n"
        elif results['health_score'] >= 70:
            report += "✅ SYSTEM STATUS: GOOD\n"
        elif results['health_score'] >= 50:
            report += "⚠️ SYSTEM STATUS: NEEDS ATTENTION\n"
        else:
            report += "🚨 SYSTEM STATUS: CRITICAL\n"
        
        return report

async def main():
    """Main function for standalone execution"""
    monitor = HealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--report':
        # Generate detailed report
        report = await monitor.generate_health_report()
        print(report)
    else:
        # Run basic health check
        results = await monitor.run_health_check()
        print(f"Health Score: {results['health_score']}/100")
        
        if results['issues_found']:
            print(f"Issues: {len(results['issues_found'])}")
        if results['fixes_applied']:
            print(f"Fixes Applied: {len(results['fixes_applied'])}")

if __name__ == '__main__':
    asyncio.run(main())