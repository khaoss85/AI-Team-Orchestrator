import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Set
from uuid import UUID, uuid4
import json
import time
from collections import defaultdict, Counter
import difflib

# Import da moduli del progetto
from models import TaskStatus, Task, AgentStatus, WorkspaceStatus, Agent as AgentModelPydantic
from database import (
    list_tasks,
    update_task_status,
    update_agent_status,
    get_workspace,
    get_agent,
    list_agents as db_list_agents,
    create_task,
    get_active_workspaces,
    get_workspaces_with_pending_tasks,
    update_workspace_status
)
from ai_agents.manager import AgentManager

# Import componenti per auto-generazione
from task_analyzer import EnhancedTaskExecutor

logger = logging.getLogger(__name__)

class BudgetTracker:
    """Tracks budget usage for agents with detailed cost monitoring"""

    def __init__(self):
        """Initialize the budget tracker."""
        self.usage_log: Dict[str, List[Dict[str, Any]]] = {}
        # Costi aggiornati per token per diversi modelli (valori ipotetici)
        self.token_costs = {
            "gpt-4.1": {"input": 0.03, "output": 0.06},
            "gpt-4.1-mini": {"input": 0.015, "output": 0.03},
            "gpt-4.1-nano": {"input": 0.01, "output": 0.02},
            "gpt-4-turbo": {"input": 0.02, "output": 0.04},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }
        # Modello di fallback se non specificato o non trovato
        self.default_model = "gpt-4.1-mini"
        self.default_costs = self.token_costs[self.default_model]

    def log_usage(self, agent_id: str, model: str, input_tokens: int, output_tokens: int, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Log token usage and associated costs for an agent and task."""
        if agent_id not in self.usage_log:
            self.usage_log[agent_id] = []

        # Ottieni i costi per il modello specificato, altrimenti usa il default
        costs = self.token_costs.get(model, self.default_costs)
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total_cost = input_cost + output_cost

        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent_id": agent_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD"
        }

        self.usage_log[agent_id].append(usage_record)
        logger.info(f"Budget usage - Agent {agent_id}, Task {task_id}: ${total_cost:.6f} (Model: {model}, Tokens: {input_tokens} in + {output_tokens} out)")
        return usage_record

    def get_agent_total_cost(self, agent_id: str) -> float:
        """Calculate the total cost incurred by a specific agent."""
        if agent_id not in self.usage_log:
            return 0.0
        return sum(record["total_cost"] for record in self.usage_log[agent_id])

    def get_workspace_total_cost(self, workspace_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Calculate the total cost incurred within a workspace, broken down by agent."""
        total_cost = 0.0
        agent_costs = {}
        total_tokens = {"input": 0, "output": 0}

        for agent_id in agent_ids:
            agent_total_cost = self.get_agent_total_cost(agent_id)
            agent_costs[agent_id] = round(agent_total_cost, 6)
            total_cost += agent_total_cost

            # Accumula i token per l'agente
            agent_input_tokens = 0
            agent_output_tokens = 0
            if agent_id in self.usage_log:
                for record in self.usage_log[agent_id]:
                    agent_input_tokens += record["input_tokens"]
                    agent_output_tokens += record["output_tokens"]
            total_tokens["input"] += agent_input_tokens
            total_tokens["output"] += agent_output_tokens

        return {
            "workspace_id": workspace_id,
            "total_cost": round(total_cost, 6),
            "agent_costs": agent_costs,
            "total_tokens": total_tokens,
            "currency": "USD"
        }

    def get_all_usage_logs(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all usage logs, optionally filtered by agent."""
        if agent_id:
            return self.usage_log.get(agent_id, [])
        else:
            all_logs = []
            for logs in self.usage_log.values():
                all_logs.extend(logs)
            return all_logs


class TaskExecutor:
    """Enhanced Task Executor with runaway protection and better monitoring"""

    def __init__(self):
        """Initialize the enhanced task executor."""
        self.running = False
        self.paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.workspace_managers: Dict[UUID, AgentManager] = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log: List[Dict[str, Any]] = []

        # Configurazione concorrenza e coda
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", 3))
        self.max_queue_size = self.max_concurrent_tasks * 10
        self.active_tasks_count = 0
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.worker_tasks: List[asyncio.Task] = []

        # Componenti per automazione
        self.enhanced_handler = EnhancedTaskExecutor()

        # AGGIUNTE per runaway protection
        self.workspace_auto_generation_paused: Set[str] = set()
        self.workspace_task_counts: Dict[str, Dict[str, int]] = {}
        self.last_runaway_check: Optional[datetime] = None
        
        # Configurazione runaway protection
        self.max_pending_tasks_per_workspace = int(os.getenv("MAX_PENDING_TASKS", 50))
        self.max_handoff_percentage = float(os.getenv("MAX_HANDOFF_PERCENTAGE", 0.3))
        self.runaway_check_interval = 300  # 5 minuti

    async def check_workspace_health(self, workspace_id: str) -> Dict[str, Any]:
        """Enhanced workspace health check with pattern recognition"""
        try:
            all_tasks = await list_tasks(workspace_id)
            agents = await db_list_agents(workspace_id)
            
            # Conta task per status
            task_counts = {
                'total': len(all_tasks),
                'pending': len([t for t in all_tasks if t.get("status") == TaskStatus.PENDING.value]),
                'completed': len([t for t in all_tasks if t.get("status") == TaskStatus.COMPLETED.value]),
                'failed': len([t for t in all_tasks if t.get("status") == TaskStatus.FAILED.value]),
                'in_progress': len([t for t in all_tasks if t.get("status") == TaskStatus.IN_PROGRESS.value])
            }
            
            # Analisi pattern dettagliata
            pattern_analysis = self._analyze_task_patterns(all_tasks)
            health_issues = []
            
            # 1. DETECTION: Excessive pending tasks
            if task_counts['pending'] > self.max_pending_tasks_per_workspace:
                health_issues.append(f"Excessive pending tasks: {task_counts['pending']}")
            
            # 2. DETECTION: High task creation velocity
            creation_velocity = self._calculate_task_creation_velocity(all_tasks)
            if creation_velocity > 5.0:  # Più di 5 task/minuto
                health_issues.append(f"High task creation rate: {creation_velocity:.1f}/min")
            
            # 3. DETECTION: Repetitive task patterns (improved)
            repeated_patterns = pattern_analysis['repeated_patterns']
            if repeated_patterns:
                health_issues.append(f"Repeated task patterns: {repeated_patterns}")
            
            # 4. DETECTION: Delegation loops
            delegation_loops = pattern_analysis['delegation_loops']
            if delegation_loops:
                health_issues.append(f"Delegation loops detected: {delegation_loops}")
            
            # 5. DETECTION: Failed handoffs
            failed_handoffs = pattern_analysis['failed_handoffs']
            if failed_handoffs > 3:
                health_issues.append(f"High handoff failure rate: {failed_handoffs} failed")
            
            # 6. DETECTION: Same-role recursion
            same_role_recursion = pattern_analysis['same_role_recursion']
            if same_role_recursion:
                health_issues.append(f"Same-role task recursion: {same_role_recursion}")
            
            # 7. NEW: Detection of task orphaning (tasks without proper agents)
            orphaned_tasks = [t for t in all_tasks if not t.get('agent_id') or 
                             not any(a['id'] == t['agent_id'] for a in agents)]
            if orphaned_tasks:
                health_issues.append(f"Orphaned tasks without agents: {len(orphaned_tasks)}")
            
            # Calcola health score migliorato
            health_score = self._calculate_improved_health_score(
                task_counts, health_issues, creation_velocity, pattern_analysis
            )
            
            return {
                'workspace_id': workspace_id,
                'task_counts': task_counts,
                'health_issues': health_issues,
                'health_score': health_score,
                'is_healthy': len(health_issues) == 0 and health_score > 70,
                'auto_generation_paused': workspace_id in self.workspace_auto_generation_paused,
                'pattern_analysis': pattern_analysis,
                'creation_velocity': creation_velocity
            }
            
        except Exception as e:
            logger.error(f"Error checking workspace health for {workspace_id}: {e}")
            return {
                'workspace_id': workspace_id,
                'error': str(e),
                'is_healthy': False,
                'health_score': 0
            }

    def _analyze_task_patterns(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Analyze task patterns for loop detection"""
        
        # Pattern 1: Repeated task names
        task_names = [t.get("name", "") for t in tasks]
        name_counts = Counter(task_names)
        repeated_patterns = {name: count for name, count in name_counts.items() 
                            if count > 3 and name}
        
        # Pattern 2: Delegation loops (A creates for B, B creates for A)
        delegation_graph = defaultdict(list)
        delegation_loops = []
        
        # Analizza delegation patterns dai log dell'executor
        recent_activity = self.get_recent_activity(tasks[0].get('workspace_id') if tasks else None, 100)
        
        for activity in recent_activity:
            if activity.get('event') == 'subtask_delegated':
                details = activity.get('details', {})
                source = details.get('delegated_by', '')
                target = details.get('assigned_agent_name', '')
                if source and target:
                    delegation_graph[source].append(target)
        
        # Detect cycles in delegation graph
        for source, targets in delegation_graph.items():
            for target in targets:
                if source in delegation_graph.get(target, []):
                    delegation_loops.append(f"{source} ↔ {target}")
        
        # Pattern 3: Failed handoffs
        failed_handoffs = sum(1 for activity in recent_activity 
                             if activity.get('event') == 'handoff_created' and 
                                'escalation' in activity.get('details', {}).get('handoff_type', ''))
        
        # Pattern 4: Same-role recursion (task created by same role for same role)
        same_role_recursion = []
        for activity in recent_activity:
            if activity.get('event') == 'subtask_delegated':
                details = activity.get('details', {})
                # Se il ruolo richiesto è simile al ruolo che ha creato
                source_role = details.get('source_agent_role', '').lower()
                target_role = details.get('target_role', '').lower()
                if source_role and target_role and source_role in target_role:
                    same_role_recursion.append(f"{source_role} → {target_role}")
        
        # Pattern 5: Task description similarity (nuova detection)
        description_clusters = self._find_similar_descriptions(tasks)
        
        return {
            'repeated_patterns': repeated_patterns,
            'delegation_loops': delegation_loops,
            'failed_handoffs': failed_handoffs,
            'same_role_recursion': list(set(same_role_recursion)),
            'description_clusters': description_clusters
        }

    def _find_similar_descriptions(self, tasks: List[Dict]) -> List[Dict]:
        """Find tasks with similar descriptions that might indicate loops"""
        import difflib
        
        clusters = []
        processed = set()
        
        for i, task1 in enumerate(tasks):
            if i in processed:
                continue
                
            desc1 = task1.get('description', '')[:200].lower()
            if not desc1:
                continue
                
            similar_tasks = [task1]
            processed.add(i)
            
            for j, task2 in enumerate(tasks[i+1:], i+1):
                if j in processed:
                    continue
                    
                desc2 = task2.get('description', '')[:200].lower()
                if not desc2:
                    continue
                
                # Calcola similarità
                similarity = difflib.SequenceMatcher(None, desc1, desc2).ratio()
                if similarity > 0.7:  # 70% similar
                    similar_tasks.append(task2)
                    processed.add(j)
            
            if len(similar_tasks) > 1:
                clusters.append({
                    'count': len(similar_tasks),
                    'sample_names': [t.get('name', '') for t in similar_tasks[:3]],
                    'similarity_score': similarity
                })
        
        return clusters

    def _calculate_task_creation_velocity(self, tasks: List[Dict]) -> float:
        """Calculate task creation velocity (tasks/minute) in recent period"""
        if not tasks:
            return 0.0
        
        # Analizza ultimi 30 minuti
        now = datetime.now()
        recent_tasks = []
        
        for task in tasks:
            created_at_str = task.get('created_at')
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if now - created_at < timedelta(minutes=30):
                        recent_tasks.append(created_at)
                except:
                    continue
        
        if len(recent_tasks) < 2:
            return 0.0
        
        # Calcola velocità nell'ultimo periodo con task
        recent_tasks.sort()
        time_span = (recent_tasks[-1] - recent_tasks[0]).total_seconds()
        
        if time_span > 0:
            return (len(recent_tasks) / time_span) * 60  # tasks per minute
        return 0.0

    def _calculate_improved_health_score(
        self, 
        task_counts: Dict,
        health_issues: List[str],
        creation_velocity: float,
        pattern_analysis: Dict
    ) -> float:
        """Calculate improved health score (0-100)"""
        
        score = 100.0
        
        # Penalty for health issues (major factor)
        score -= len(health_issues) * 15
        
        # Penalty for high pending ratio
        if task_counts['total'] > 0:
            pending_ratio = task_counts['pending'] / task_counts['total']
            if pending_ratio > 0.5:
                score -= (pending_ratio - 0.5) * 40
        
        # Penalty for creation velocity
        if creation_velocity > 3.0:
            score -= min((creation_velocity - 3.0) * 10, 30)
        
        # Bonus for task completion
        if task_counts['total'] > 0:
            completion_ratio = task_counts['completed'] / task_counts['total']
            score += completion_ratio * 20
        
        # Penalty for pattern issues
        if pattern_analysis['repeated_patterns']:
            score -= len(pattern_analysis['repeated_patterns']) * 5
        
        if pattern_analysis['delegation_loops']:
            score -= len(pattern_analysis['delegation_loops']) * 10
        
        if pattern_analysis['description_clusters']:
            score -= len(pattern_analysis['description_clusters']) * 5
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))

    async def periodic_runaway_check(self):
        """Enhanced periodic runaway check with pattern recognition"""
        try:
            active_workspaces = await get_active_workspaces()
            
            runaway_detected = []
            warning_workspaces = []
            
            for workspace_id in active_workspaces:
                health_status = await self.check_workspace_health(workspace_id)
                
                # Classification logic migliorata
                health_score = health_status['health_score']
                health_issues = health_status['health_issues']
                
                # CRITICAL: Immediate pause needed
                critical_indicators = [
                    health_score < 30,
                    health_status['task_counts']['pending'] > 50,
                    any('High task creation rate' in issue for issue in health_issues),
                    any('Delegation loops' in issue for issue in health_issues)
                ]
                
                if any(critical_indicators) and workspace_id not in self.workspace_auto_generation_paused:
                    runaway_detected.append({
                        'workspace_id': workspace_id,
                        'health_score': health_score,
                        'critical_issues': [issue for issue in health_issues if any(term in issue.lower() 
                                           for term in ['high task creation', 'delegation loops', 'excessive pending'])]
                    })
                    
                    await self._pause_auto_generation_for_workspace(
                        workspace_id, 
                        reason=f"Critical health issues detected (score: {health_score})"
                    )
                
                # WARNING: Monitor closely
                elif health_score < 60 and health_issues:
                    warning_workspaces.append({
                        'workspace_id': workspace_id,
                        'health_score': health_score,
                        'issues': health_issues
                    })
            
            # Log summary
            if runaway_detected:
                logger.critical(f"RUNAWAY DETECTED: {len(runaway_detected)} workspaces paused")
                for item in runaway_detected:
                    logger.critical(f"  - {item['workspace_id']}: score={item['health_score']}, issues={item['critical_issues']}")
            
            if warning_workspaces:
                logger.warning(f"WORKSPACES AT RISK: {len(warning_workspaces)} need monitoring")
                for item in warning_workspaces:
                    logger.warning(f"  - {item['workspace_id']}: score={item['health_score']}")
            
            if not runaway_detected and not warning_workspaces:
                logger.info(f"All {len(active_workspaces)} workspaces healthy")
            
            self.last_runaway_check = datetime.now()
            
            # Report per monitoring dashboard
            return {
                'timestamp': datetime.now().isoformat(),
                'total_workspaces': len(active_workspaces),
                'runaway_detected': len(runaway_detected),
                'warnings': len(warning_workspaces),
                'paused_workspaces': len(self.workspace_auto_generation_paused),
                'runaway_details': runaway_detected,
                'warning_details': warning_workspaces
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced runaway check: {e}", exc_info=True)
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    async def create_initial_workspace_task(self, workspace_id: str) -> Optional[str]:
        """Enhanced initial task creation with better project structuring"""
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace:
                logger.error(f"Workspace {workspace_id} not found when trying to create initial task.")
                return None

            agents = await db_list_agents(workspace_id)
            if not agents:
                logger.warning(f"No agents found for workspace {workspace_id}. Cannot create initial task.")
                return None

            # Analisi migliore del team e selezione del leader
            team_analysis = self._analyze_team_composition(agents)
            project_lead = self._select_project_lead(agents, team_analysis)
            
            if not project_lead:
                logger.error(f"No suitable project lead found for workspace {workspace_id}")
                return None

            logger.info(f"Selected {project_lead['name']} ({project_lead['role']}) as project lead for workspace {workspace_id}")

            # Crea task iniziale strutturato per evitare deleghe immediate caotiche
            initial_task_description = self._create_structured_initial_task(
                workspace, project_lead, team_analysis
            )

            # Crea il task nel database
            initial_task_dict = await create_task(
                workspace_id=workspace_id,
                agent_id=project_lead["id"],
                name="Project Setup & Strategic Planning",
                description=initial_task_description,
                status=TaskStatus.PENDING.value,
            )

            if initial_task_dict and initial_task_dict.get("id"):
                task_id = initial_task_dict["id"]
                logger.info(f"Created structured initial task {task_id} for workspace {workspace_id}")
                
                # Log event di creazione
                creation_log = {
                    "timestamp": datetime.now().isoformat(),
                    "event": "structured_initial_task_created",
                    "task_id": task_id,
                    "agent_id": project_lead["id"],
                    "workspace_id": workspace_id,
                    "task_name": initial_task_dict.get("name"),
                    "assigned_role": project_lead["role"],
                    "team_size": len(agents),
                    "team_composition": team_analysis
                }
                self.execution_log.append(creation_log)
                return task_id
            else:
                logger.error(f"Failed to create initial task in database for workspace {workspace_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating initial task for workspace {workspace_id}: {e}", exc_info=True)
            return None

    def _analyze_team_composition(self, agents: List[Dict]) -> Dict[str, Any]:
        """Analyze team composition to understand capabilities"""
        
        composition = {
            'total_agents': len(agents),
            'by_seniority': {'junior': 0, 'senior': 0, 'expert': 0},
            'by_role_type': defaultdict(int),
            'available_domains': set(),
            'leadership_candidates': [],
            'specialists': []
        }
        
        for agent in agents:
            # Count by seniority
            seniority = agent.get('seniority', 'junior')
            composition['by_seniority'][seniority] += 1
            
            # Extract role type and domain
            role = agent.get('role', '')
            role_lower = role.lower()
            
            # Categorize role types
            if any(term in role_lower for term in ['manager', 'coordinator', 'lead', 'director']):
                composition['by_role_type']['leadership'] += 1
                composition['leadership_candidates'].append(agent)
            elif 'analyst' in role_lower:
                composition['by_role_type']['analyst'] += 1
                composition['specialists'].append(agent)
            elif 'researcher' in role_lower:
                composition['by_role_type']['researcher'] += 1
                composition['specialists'].append(agent)
            elif 'specialist' in role_lower:
                composition['by_role_type']['specialist'] += 1
                composition['specialists'].append(agent)
            else:
                composition['by_role_type']['other'] += 1
            
            # Extract domain
            domain = self._extract_domain_from_role(role)
            if domain:
                composition['available_domains'].add(domain)
        
        composition['available_domains'] = list(composition['available_domains'])
        return composition

    def _select_project_lead(self, agents: List[Dict], team_analysis: Dict) -> Optional[Dict]:
        """Select best project lead based on role and seniority"""
        
        # Priority 1: Designated managers/coordinators
        leadership_candidates = team_analysis['leadership_candidates']
        if leadership_candidates:
            # Select most senior leader
            return max(leadership_candidates, 
                      key=lambda x: {'expert': 3, 'senior': 2, 'junior': 1}.get(x.get('seniority', 'junior'), 1))
        
        # Priority 2: Senior/Expert agents who can coordinate
        coordinatable_agents = [
            agent for agent in agents 
            if agent.get('seniority') in ['senior', 'expert'] and
               any(term in agent.get('role', '').lower() for term in ['analyst', 'lead', 'strategist'])
        ]
        
        if coordinatable_agents:
            return max(coordinatable_agents,
                      key=lambda x: {'expert': 3, 'senior': 2, 'junior': 1}.get(x.get('seniority', 'junior'), 1))
        
        # Priority 3: Any senior agent
        senior_agents = [agent for agent in agents if agent.get('seniority') in ['senior', 'expert']]
        if senior_agents:
            return senior_agents[0]
        
        # Fallback: First agent
        return agents[0] if agents else None

    def _create_structured_initial_task(
        self, 
        workspace: Dict, 
        project_lead: Dict, 
        team_analysis: Dict
    ) -> str:
        """Create a well-structured initial task that minimizes chaotic delegation"""
        
        workspace_goal = workspace.get('goal', 'No goal specified')
        budget_info = workspace.get('budget', {})
        team_size = team_analysis['total_agents']
        available_domains = team_analysis['available_domains']
        
        # Crea template basato sulla composizione del team
        task_description = f"""
**PROJECT INITIATION & STRATEGIC SETUP**

**PROJECT OVERVIEW**
Goal: {workspace_goal}
Budget: {budget_info.get('max_amount', 'N/A')} {budget_info.get('currency', '')} ({budget_info.get('strategy', 'Standard strategy')})
Team Size: {team_size} agents
Available Domains: {', '.join(available_domains)}

**YOUR ROLE AS PROJECT LEAD**
You are {project_lead['name']} ({project_lead['role']}) - responsible for project coordination and strategic planning.

**PHASE 1: STRATEGIC PLANNING (REQUIRED)**
Complete this phase BEFORE any delegation:

1. **Project Analysis**
   - Break down the main goal into 3-5 major phases
   - Identify key deliverables for each phase
   - Assess resource requirements and timeline

2. **Team Mapping**
   - Review available agents and their specializations
   - Map phases to appropriate specialists
   - Identify any capability gaps

3. **Execution Strategy**
   - Define clear handoff points between agents
   - Establish success criteria for each phase
   - Create workflow to minimize back-and-forth delegation

**PHASE 2: CONTROLLED DELEGATION (AFTER PLANNING)**
Only after completing Phase 1 analysis:

4. **Create Specific Tasks** (not general ones)
   - Create concrete, well-defined tasks for specialists
   - Include clear input requirements and expected outputs
   - Specify dependencies and handoff requirements

5. **Establish Coordination Protocol**
   - Set up regular check-ins or progress monitoring
   - Define escalation paths for issues
   - Ensure each specialist knows their specific scope

**TEAM COMPOSITION ANALYSIS**
{self._format_team_composition_for_task(team_analysis)}

**OUTPUT REQUIREMENTS**
Provide a comprehensive project plan including:
1. Phase breakdown with clear deliverables
2. Task assignments with rationale
3. Timeline and dependency map
4. Risk assessment and mitigation strategies
5. Coordination protocol for team management

**CRITICAL INSTRUCTIONS**
- COMPLETE the strategic planning before delegating any tasks
- Create SPECIFIC tasks (not "analyze X" but "analyze X to determine Y for decision Z")
- Ensure each task has clear inputs, processes, and outputs
- Avoid creating duplicate or overlapping tasks
- Focus on PROJECT COMPLETION not endless iteration

**SUCCESS CRITERIA**
This initial phase is successful when:
- Clear project roadmap exists
- All team members have specific, actionable tasks
- Workflow minimizes hand-offs and delegation
- Project can proceed without coordinator micro-management
"""
        
        return task_description.strip()

    def _format_team_composition_for_task(self, team_analysis: Dict) -> str:
        """Format team composition for inclusion in task description"""
        
        lines = []
        lines.append(f"Total Team: {team_analysis['total_agents']} agents")
        
        # Seniority breakdown
        seniority = team_analysis['by_seniority']
        lines.append(f"Seniority: {seniority['expert']} Expert, {seniority['senior']} Senior, {seniority['junior']} Junior")
        
        # Role types
        role_types = team_analysis['by_role_type']
        lines.append("Role Distribution:")
        for role_type, count in role_types.items():
            if count > 0:
                lines.append(f"  - {role_type.title()}: {count}")
        
        # Available domains
        if team_analysis['available_domains']:
            lines.append(f"Domains: {', '.join(team_analysis['available_domains'])}")
        
        # Key specialists
        if team_analysis['specialists']:
            lines.append("Key Specialists:")
            for specialist in team_analysis['specialists'][:3]:  # Top 3
                lines.append(f"  - {specialist['name']}: {specialist['role']}")
        
        return '\n'.join(lines)

    def _extract_domain_from_role(self, role: str) -> Optional[str]:
        """Extract domain from role - same as in specialist.py"""
        role_lower = role.lower()
        
        domains = {
            'finance': ['financial', 'finance', 'investment', 'accounting', 'budget'],
            'marketing': ['marketing', 'brand', 'campaign', 'promotion', 'social'],
            'sales': ['sales', 'revenue', 'customer', 'client', 'business'],
            'product': ['product', 'development', 'design', 'engineering'],
            'data': ['data', 'analytics', 'statistics', 'insights', 'intelligence'],
            'hr': ['human resources', 'hr', 'talent', 'recruitment', 'people'],
            'operations': ['operations', 'process', 'workflow', 'logistics'],
            'strategy': ['strategy', 'strategic', 'planning', 'vision'],
            'content': ['content', 'writing', 'editorial', 'copy'],
            'research': ['research', 'investigation', 'study', 'analysis'],
            'sports': ['sports', 'athletic', 'performance', 'fitness', 'competition'],
            'technology': ['technology', 'tech', 'software', 'system', 'development']
        }
        
        for domain, keywords in domains.items():
            if any(keyword in role_lower for keyword in keywords):
                return domain
        
        return None

    async def _pause_auto_generation_for_workspace(self, workspace_id: str, reason: str = "runaway_detected"):
        """Mette in pausa l'auto-generazione per un workspace"""
        self.workspace_auto_generation_paused.add(workspace_id)
        
        # Log critico
        logger.critical(f"AUTO-GENERATION PAUSED for workspace {workspace_id}. Reason: {reason}")
        
        # Aggiorna stato workspace se necessario
        try:
            workspace = await get_workspace(workspace_id)
            if workspace and workspace.get("status") == "active":
                await update_workspace_status(workspace_id, "needs_intervention")
                logger.info(f"Updated workspace {workspace_id} status to 'needs_intervention'")
        except Exception as e:
            logger.error(f"Failed to update workspace status for {workspace_id}: {e}")
        
        # Notifica via log evento speciale per monitoring
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "auto_generation_paused", 
            "workspace_id": workspace_id,
            "reason": reason,
            "pending_tasks_count": len(await list_tasks(workspace_id))
        })

    async def _resume_auto_generation_for_workspace(self, workspace_id: str):
        """Riprende l'auto-generazione per un workspace"""
        if workspace_id in self.workspace_auto_generation_paused:
            self.workspace_auto_generation_paused.remove(workspace_id)
            logger.info(f"AUTO-GENERATION RESUMED for workspace {workspace_id}")
            
            # Log dell'evento
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "auto_generation_resumed",
                "workspace_id": workspace_id
            })

    async def start(self):
        """Start the task executor service."""
        if self.running:
            logger.warning("Task executor is already running.")
            return

        self.running = True
        self.paused = False
        self.pause_event.set()
        self.execution_log = []
        logger.info(f"Starting enhanced task executor. Max concurrent tasks: {self.max_concurrent_tasks}, Max queue size: {self.max_queue_size}")

        # Avvia i worker per processare la coda
        self.worker_tasks = [asyncio.create_task(self._task_worker()) for _ in range(self.max_concurrent_tasks)]

        # Avvia il loop principale di gestione
        asyncio.create_task(self.execution_loop())
        logger.info("Enhanced task executor started successfully.")

    async def stop(self):
        """Stop the task executor service gracefully."""
        if not self.running:
            logger.warning("Task executor is not running.")
            return

        logger.info("Stopping task executor...")
        self.running = False
        self.paused = True
        self.pause_event.set()

        # Invia segnali di terminazione ai worker
        for i in range(len(self.worker_tasks)):
            try:
                await asyncio.wait_for(self.task_queue.put(None), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout putting None signal in task_queue during stop (worker {i+1}/{len(self.worker_tasks)}).")
            except asyncio.QueueFull:
                 logger.warning(f"Queue full trying to put None signal during stop (worker {i+1}/{len(self.worker_tasks)}). May cause delay.")

        # Attendi il completamento dei worker
        if self.worker_tasks:
            results = await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.error(f"Worker task {i} finished with error during stop: {result}", exc_info=result)
        self.worker_tasks = []
        logger.info("Task executor stopped.")

    async def pause(self):
        """Pause task processing. Workers finish current tasks but don't pick new ones."""
        if not self.running:
            logger.warning("Cannot pause: Task executor is not running.")
            return
        if self.paused:
            logger.info("Task executor is already paused.")
            return
        self.paused = True
        self.pause_event.clear()
        logger.info("Task executor paused. New task processing suspended. Workers will finish current tasks.")

    async def resume(self):
        """Resume task processing if paused."""
        if not self.running:
            logger.warning("Cannot resume: Task executor is not running. Start it first.")
            return
        if not self.paused:
            logger.info("Task executor is already running (not paused).")
            return
        self.paused = False
        self.pause_event.set()
        logger.info("Task executor resumed.")

    async def execution_loop(self):
        """Main loop with periodic runaway checks"""
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running: 
                    break
                
                # Main execution logic
                logger.debug("Execution loop running: checking for tasks and workspaces.")
                await self.process_all_pending_tasks()
                await self.check_for_new_workspaces()
                
                # AGGIUNTA: Periodic runaway check ogni 5 minuti
                if (self.last_runaway_check is None or 
                    (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                    await self.periodic_runaway_check()
                
                # Attesa normale
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                logger.info("Execution loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in execution_loop: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Execution loop finished.")

    async def _task_worker(self):
        """Worker process that takes tasks from the queue and executes them."""
        worker_id = uuid4()
        logger.info(f"Task worker {worker_id} started.")
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running: break

                manager: Optional[AgentManager] = None
                task_dict: Optional[Dict] = None
                try:
                    manager, task_dict = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if task_dict is None:
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} received termination signal.")
                    break

                task_id = task_dict.get("id", "UnknownID")
                workspace_id = task_dict.get("workspace_id", "UnknownWS")
                logger.info(f"Worker {worker_id} picking up task: {task_id} from Workspace {workspace_id} (Queue size: {self.task_queue.qsize()})")

                # Incrementa contatore task attivi e esegui
                self.active_tasks_count += 1
                try:
                    if manager is None:
                         raise ValueError(f"Received task {task_id} with a null manager.")
                    await self.execute_task_with_tracking(manager, task_dict)
                except Exception as e_exec:
                    logger.error(f"Worker {worker_id} failed executing task {task_id}: {e_exec}", exc_info=True)
                finally:
                    self.active_tasks_count -= 1
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} finished processing task: {task_id}. Active tasks: {self.active_tasks_count}")

            except asyncio.CancelledError:
                logger.info(f"Task worker {worker_id} cancelled.")
                break
            except Exception as e_worker:
                logger.error(f"Unhandled error in task worker {worker_id}: {e_worker}", exc_info=True)
                await asyncio.sleep(5)

        logger.info(f"Task worker {worker_id} exiting.")

    async def check_for_new_workspaces(self):
        """Check for active workspaces without any tasks and create an initial one."""
        if self.paused: return

        try:
            logger.debug("Checking for workspaces needing initial tasks")
            active_ws_ids = await get_active_workspaces()

            for ws_id in active_ws_ids:
                tasks = await list_tasks(ws_id)
                if not tasks:
                    workspace_data = await get_workspace(ws_id)
                    if workspace_data and workspace_data.get("status") == WorkspaceStatus.ACTIVE.value:
                        logger.info(f"Workspace {ws_id} ('{workspace_data.get('name')}') is active and has no tasks. Attempting to create initial task.")
                        await self.create_initial_workspace_task(ws_id)
                    elif not workspace_data:
                         logger.warning(f"Could not retrieve data for supposedly active workspace {ws_id} during initial task check.")

        except Exception as e:
            logger.error(f"Error checking for new workspaces: {e}", exc_info=True)

    async def process_all_pending_tasks(self):
        """Find workspaces with pending tasks and queue them for processing."""
        if self.paused: return

        try:
            logger.debug("Processing all pending tasks")
            workspaces_with_pending = await get_workspaces_with_pending_tasks()

            if workspaces_with_pending:
                 logger.info(f"Found {len(workspaces_with_pending)} workspaces with pending tasks. Checking queue status.")

            for workspace_id in workspaces_with_pending:
                if self.task_queue.full():
                    logger.warning(f"Task queue is full (Size: {self.task_queue.qsize()}/{self.max_queue_size}). Skipping adding tasks from workspace {workspace_id} for now.")
                    continue

                await self.process_workspace_tasks(workspace_id)

        except Exception as e:
            logger.error(f"Error processing all pending tasks: {e}", exc_info=True)

    async def process_workspace_tasks(self, workspace_id: str):
        """Fetch pending tasks with enhanced runaway protection"""
        if self.paused: 
            return
        
        try:
            # STEP 1: Health check completo
            health_status = await self.check_workspace_health(workspace_id)
            
            # Se workspace non è healthy, gestisci
            if not health_status['is_healthy']:
                health_issues = health_status['health_issues']
                logger.warning(f"Workspace {workspace_id} health issues: {health_issues}")
                
                # Se ci sono problemi gravi, pausa auto-generazione
                critical_issues = [issue for issue in health_issues if any(keyword in issue.lower() 
                    for keyword in ['excessive pending', 'excessive handoffs', 'high task creation'])]
                
                if critical_issues and workspace_id not in self.workspace_auto_generation_paused:
                    await self._pause_auto_generation_for_workspace(workspace_id, 
                        reason=f"Health issues: {'; '.join(critical_issues)}")
                    return
            
            # STEP 2: Se auto-generation è pausata, controlla se si può riprendere
            if workspace_id in self.workspace_auto_generation_paused:
                # Controlla se i problemi sono risolti
                if health_status['is_healthy'] and health_status['task_counts']['pending'] < 10:
                    await self._resume_auto_generation_for_workspace(workspace_id)
                else:
                    logger.info(f"Auto-generation still paused for {workspace_id}. "
                               f"Pending: {health_status['task_counts']['pending']}")
                    return
            
            # STEP 3: Processa task normalmente
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"Failed to get agent manager for workspace {workspace_id}")
                return
            
            # Get pending tasks
            tasks_db = await list_tasks(workspace_id)
            pending_tasks_dicts = [task for task in tasks_db if task.get("status") == TaskStatus.PENDING.value]
            
            if not pending_tasks_dicts:
                return
            
            # STEP 4: Batch processing per evitare sovraccarico
            batch_size = min(3, len(pending_tasks_dicts))  # Ridotto da 5 a 3 per maggiore controllo
            tasks_to_process = pending_tasks_dicts[:batch_size]
            
            logger.info(f"Processing {len(tasks_to_process)}/{len(pending_tasks_dicts)} tasks for workspace {workspace_id}")
            
            queued_count = 0
            for task_dict in tasks_to_process:
                if self.task_queue.full():
                    logger.warning(f"Queue full, stopping task processing for workspace {workspace_id}")
                    break
                
                try:
                    self.task_queue.put_nowait((manager, task_dict))
                    queued_count += 1
                except asyncio.QueueFull:
                    logger.warning(f"Queue full during processing for workspace {workspace_id}")
                    break
            
            if queued_count > 0:
                logger.info(f"Successfully queued {queued_count} tasks for workspace {workspace_id}")
            
            # STEP 5: Update workspace task counts per tracking
            self.workspace_task_counts[workspace_id] = health_status['task_counts']
            
        except Exception as e:
            logger.error(f"Error processing tasks for workspace {workspace_id}: {e}", exc_info=True)

    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        """Get or create an AgentManager instance for a given workspace ID."""
        try:
            workspace_uuid = UUID(workspace_id)
        except ValueError:
            logger.error(f"Invalid workspace ID format: {workspace_id}. Cannot get/create manager.")
            return None

        if workspace_uuid in self.workspace_managers:
            return self.workspace_managers[workspace_uuid]

        logger.info(f"Creating new AgentManager instance for workspace {workspace_id}.")
        try:
            manager = AgentManager(workspace_uuid)
            success = await manager.initialize()

            if success:
                self.workspace_managers[workspace_uuid] = manager
                logger.info(f"Initialized agent manager for workspace {workspace_id}")
                return manager
            else:
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}. Check logs for details from AgentManager.")
                return None
        except Exception as e:
            logger.error(f"Exception creating or initializing agent manager for workspace {workspace_id}: {e}", exc_info=True)
            return None

    async def execute_task_with_tracking(self, manager: AgentManager, task_dict: dict):
        """Executes a single task, tracks budget, logs events, and triggers post-processing."""
        task_id = task_dict.get("id")

        # Aggiungi controllo per task duplicati PER WORKSPACE
        workspace_id = task_dict.get("workspace_id")

        # Inizializza il tracking per workspace se non esiste
        if not hasattr(self, '_processed_tasks_by_workspace'):
            self._processed_tasks_by_workspace = {}

        # Inizializza set per questo workspace
        if workspace_id not in self._processed_tasks_by_workspace:
            self._processed_tasks_by_workspace[workspace_id] = set()

        # Controlla se task già processato in questo workspace
        if task_id in self._processed_tasks_by_workspace[workspace_id]:
            logger.warning(f"Task {task_id} already processed in workspace {workspace_id}, skipping")
            return

        # Aggiungi task al set di quelli processati
        self._processed_tasks_by_workspace[workspace_id].add(task_id)

        agent_id = task_dict.get("agent_id")

        # Validazione preliminare
        if not all([task_id, agent_id, workspace_id]):
            missing = [k for k, v in {'task_id': task_id, 'agent_id': agent_id, 'workspace_id': workspace_id}.items() if not v]
            error_msg = f"Task data incomplete: missing {', '.join(missing)}. Cannot execute."
            logger.error(error_msg)
            if task_id:
                try:
                    await update_task_status(task_id, TaskStatus.FAILED.value, {"error": error_msg, "status_detail": "invalid_task_data"})
                except Exception as db_err:
                    logger.error(f"Failed to update status for invalid task {task_id}: {db_err}")
            return

        start_time_tracking = time.time()
        model_for_budget = "unknown"
        estimated_input_tokens = 0

        try:
            # Log inizio esecuzione
            execution_start_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_started",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "task_name": task_dict.get("name", "N/A")
            }
            self.execution_log.append(execution_start_log)
            await update_task_status(task_id, TaskStatus.IN_PROGRESS.value, {"detail": "Execution started by worker"})

            # Recupera dati agente per determinare il modello
            agent_data_db = await get_agent(agent_id)
            if not agent_data_db:
                raise ValueError(f"Agent {agent_id} not found in database.")

            # Determina il modello LLM da usare (e per il budget)
            llm_config = agent_data_db.get("llm_config", {})
            model_for_budget = llm_config.get("model")
            if not model_for_budget:
                seniority_map = {"junior": "gpt-4.1-nano", "senior": "gpt-4.1-mini", "expert": "gpt-4.1"}
                model_for_budget = seniority_map.get(agent_data_db.get("seniority", "senior"), self.budget_tracker.default_model)
            logger.info(f"Executing task {task_id} ('{task_dict.get('name')}') with agent {agent_id} (Role: {agent_data_db.get('role', 'N/A')}) using model {model_for_budget}")

            # Stima input tokens
            task_input_text = f"{task_dict.get('name', '')} {task_dict.get('description', '')}"
            estimated_input_tokens = max(1, len(task_input_text) // 4)

            # Costruisci l'oggetto Task Pydantic
            try:
                task_pydantic_obj = Task(
                    id=UUID(task_id),
                    workspace_id=UUID(workspace_id),
                    agent_id=UUID(agent_id),
                    name=task_dict.get("name", "N/A"),
                    description=task_dict.get("description", ""),
                    status=TaskStatus.IN_PROGRESS,
                    created_at=datetime.fromisoformat(task_dict["created_at"]) if task_dict.get("created_at") else datetime.now(),
                    updated_at=datetime.now(),
                    result=task_dict.get("result"),
                )
            except (ValueError, TypeError, KeyError) as pydantic_error:
                logger.error(f"Error creating Pydantic Task object for task {task_id}: {pydantic_error}", exc_info=True)
                raise ValueError("Internal error preparing task object.") from pydantic_error

            # --- ESECUZIONE EFFETTIVA DEL TASK ---
            result_from_agent: Dict[str, Any] = await manager.execute_task(task_pydantic_obj.id)
            # ------------------------------------

            execution_time = time.time() - start_time_tracking

            # Estrai/stima output tokens e gestisci il risultato
            result_output = result_from_agent.get("output", "Task completed without explicit output.") if isinstance(result_from_agent, dict) else str(result_from_agent)
            actual_output_tokens = result_from_agent.get("usage", {}).get("output_tokens")
            estimated_output_tokens = actual_output_tokens if actual_output_tokens is not None else max(1, len(str(result_output)) // 4)
            actual_input_tokens = result_from_agent.get("usage", {}).get("input_tokens")
            final_input_tokens = actual_input_tokens if actual_input_tokens is not None else estimated_input_tokens

            # Log budget usage
            usage_record = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_budget,
                input_tokens=final_input_tokens,
                output_tokens=estimated_output_tokens,
                task_id=task_id
            )

            # Prepara il payload del risultato da salvare nel DB
            task_result_payload_for_db = {
                "output": result_output,
                "status_detail": "completed_successfully",
                "execution_time_seconds": round(execution_time, 2),
                "model_used": model_for_budget,
                "tokens_used": {
                     "input": final_input_tokens,
                     "output": estimated_output_tokens,
                     "estimated": actual_input_tokens is None or actual_output_tokens is None
                 },
                "cost_estimated": usage_record["total_cost"],
                "agent_metadata": result_from_agent.get("metadata")
            }
            await update_task_status(task_id, TaskStatus.COMPLETED.value, task_result_payload_for_db)

            # Log fine esecuzione
            result_summary = (str(result_output)[:150] + "...") if len(str(result_output)) > 150 else str(result_output)
            execution_end_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_completed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "task_name": task_dict.get("name", "N/A"),
                "execution_time": round(execution_time, 2),
                "cost": usage_record["total_cost"], "model": model_for_budget,
                "tokens_used": {"input": usage_record["input_tokens"], "output": usage_record["output_tokens"]},
                "result_summary": result_summary
            }
            self.execution_log.append(execution_end_log)
            logger.info(f"Task {task_id} completed. Cost: ${usage_record['total_cost']:.6f}, Time: {execution_time:.2f}s")

            # --- Trigger post-esecuzione (es. auto-generazione) ---
            try:
                # Crea un oggetto Task Pydantic aggiornato con lo stato COMPLETED e il risultato
                completed_task_pydantic_obj_for_handler = Task(
                    id=UUID(task_id), workspace_id=UUID(workspace_id), agent_id=UUID(agent_id),
                    name=task_dict.get("name", "N/A"), description=task_dict.get("description", ""),
                    status=TaskStatus.COMPLETED,
                    result=task_result_payload_for_db,
                    created_at=task_pydantic_obj.created_at,
                    updated_at=datetime.now(),
                )
                # Chiama l'handler passando l'oggetto Task completato e il workspace ID
                await self.enhanced_handler.handle_task_completion(
                    completed_task=completed_task_pydantic_obj_for_handler,
                    task_result=task_result_payload_for_db,
                    workspace_id=workspace_id
                )
                logger.info(f"Post-completion handler (e.g., auto-generation analysis) triggered for task {task_id}")
            except Exception as auto_error:
                logger.error(f"Error in post-completion handler for task {task_id}: {auto_error}", exc_info=True)
            # -----------------------------------------------------

        except Exception as e:
            # Gestione centralizzata degli errori durante l'esecuzione
            logger.error(f"Critical error executing task {task_id}: {e}", exc_info=True)
            execution_time_failed = time.time() - start_time_tracking

            # Stima conservativa dei token per il budget in caso di fallimento
            input_tokens_failed = estimated_input_tokens if estimated_input_tokens > 0 else 0
            output_tokens_failed = 50

            # Logga comunque il costo stimato del tentativo fallito
            usage_record_failed = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_budget,
                input_tokens=input_tokens_failed,
                output_tokens=output_tokens_failed, task_id=task_id
            )

            # Prepara payload di errore per il DB
            error_payload_for_db = {
                "error": str(e),
                "status_detail": "failed_during_execution",
                "execution_time_seconds": round(execution_time_failed, 2),
                "cost_estimated": usage_record_failed["total_cost"]
            }
            # Aggiorna lo stato del task a FAILED nel DB
            try:
                 await update_task_status(task_id, TaskStatus.FAILED.value, error_payload_for_db)
            except Exception as db_update_err:
                 logger.error(f"Failed to update task status to FAILED for task {task_id} after execution error: {db_update_err}")

            # Log dell'evento di fallimento
            execution_error_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_failed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "task_name": task_dict.get("name", "N/A"),
                "execution_time": round(execution_time_failed, 2),
                "cost": usage_record_failed["total_cost"], "error": str(e), "model": model_for_budget
            }
            self.execution_log.append(execution_error_log)

    def get_recent_activity(self, workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution log events, optionally filtered by workspace."""
        logs_to_filter = self.execution_log

        if workspace_id:
            try:
                 logs_to_filter = [log for log in logs_to_filter if log.get("workspace_id") == workspace_id]
            except ValueError:
                 logger.warning(f"Invalid workspace_id format '{workspace_id}' for filtering recent activity.")
                 return []

        # Ordina dal più recente al meno recente e limita
        logs_to_filter.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return logs_to_filter[:limit]

    def get_auto_generation_stats(self) -> Dict[str, Any]:
        """Get statistics specifically about auto-generated tasks or related events."""
        # Definisci gli eventi che indicano auto-generazione o handoff
        auto_gen_event_types = {
            "auto_task_generated",
            "follow_up_generated",
            "handoff_requested",
            "subtask_created_by_agent"
        }

        auto_gen_events = [
            log for log in self.execution_log
            if log.get("event") in auto_gen_event_types
        ]
        auto_gen_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Conta per tipo di evento
        event_counts = {}
        for event_type in auto_gen_event_types:
            event_counts[event_type] = sum(1 for log in auto_gen_events if log.get("event") == event_type)

        return {
            "total_auto_generation_related_events": len(auto_gen_events),
            "event_type_counts": event_counts,
            "recent_auto_generation_events": auto_gen_events[:10],
            "auto_generation_enabled": True
        }

    def get_runaway_protection_status(self) -> Dict[str, Any]:
        """Ritorna lo stato della runaway protection"""
        return {
            "paused_workspaces": list(self.workspace_auto_generation_paused),
            "workspace_task_counts": self.workspace_task_counts,
            "last_runaway_check": self.last_runaway_check.isoformat() if self.last_runaway_check else None,
            "protection_enabled": True,
            "max_pending_tasks": self.max_pending_tasks_per_workspace,
            "max_handoff_percentage": self.max_handoff_percentage
        }

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Gathers detailed operational statistics including runaway protection"""
        tasks_completed = 0
        tasks_failed = 0
        agent_activity: Dict[str, Dict[str, Any]] = {}

        # Processa il log di esecuzione per contare successi e fallimenti
        for log_entry in self.execution_log:
            event = log_entry.get("event")
            agent_id = log_entry.get("agent_id")
            task_id = log_entry.get("task_id")

            # Conta TUTTI i task completati/falliti, non solo quelli senza agent_id
            if event == "task_completed":
                tasks_completed += 1
            elif event == "task_failed":
                tasks_failed += 1

            # Continua solo se c'è un agent_id per le statistiche per agente
            if not agent_id:
                continue

            # Inizializza le statistiche per l'agente se non già presenti
            if agent_id not in agent_activity:
                agent_activity[agent_id] = {
                    "completed": 0,
                    "failed": 0,
                    "total_cost": 0.0,
                    "name": "Unknown",
                    "role": "Unknown"
                }

            # Aggiorna i conteggi per agente
            if event == "task_completed":
                agent_activity[agent_id]["completed"] += 1
            elif event == "task_failed":
                agent_activity[agent_id]["failed"] += 1

        # Arricchisci le statistiche degli agenti con il costo totale dal BudgetTracker
        all_agent_ids_in_stats = list(agent_activity.keys())
        for agent_id in all_agent_ids_in_stats:
             agent_total_cost = self.budget_tracker.get_agent_total_cost(agent_id)
             agent_activity[agent_id]["total_cost"] = round(agent_total_cost, 6)

        # Stato attuale dell'executor
        current_status = "stopped"
        if self.running:
            current_status = "paused" if self.paused else "running"

        base_stats = {
            "executor_status": current_status,
            "tasks_in_queue": self.task_queue.qsize(),
            "tasks_actively_processing": self.active_tasks_count,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "total_execution_log_entries": len(self.execution_log),
            "session_stats": { 
                "tasks_completed_successfully": tasks_completed,
                "tasks_failed": tasks_failed,
                "agent_activity": agent_activity
            },
            "budget_tracker_stats": {
                "tracked_agents_count": len(self.budget_tracker.usage_log),
            },
            "auto_generation_summary": self.get_auto_generation_stats()
        }
        
        # Aggiungi stats runaway protection
        base_stats.update({
            "runaway_protection": self.get_runaway_protection_status(),
            "workspace_health": {
                workspace_id: counts for workspace_id, counts in self.workspace_task_counts.items()
            }
        })
        
        return base_stats


# --- Global Instance ---
task_executor = TaskExecutor()

# --- Control Functions ---
async def start_task_executor():
    """Start the global task executor service."""
    await task_executor.start()

async def stop_task_executor():
    """Stop the global task executor service."""
    await task_executor.stop()

async def pause_task_executor():
    """Pause the global task executor."""
    await task_executor.pause()

async def resume_task_executor():
    """Resume the global task executor."""
    await task_executor.resume()

def get_executor_stats() -> Dict[str, Any]:
     """Get detailed statistics from the global task executor."""
     return task_executor.get_detailed_stats()

def get_recent_executor_activity(workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
     """Get recent activity logs, optionally filtered by workspace."""
     return task_executor.get_recent_activity(workspace_id=workspace_id, limit=limit)

async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    """Manually trigger the creation of an initial task for a specific workspace."""
    return await task_executor.create_initial_workspace_task(workspace_id)

# NUOVO: Endpoint per controllo manuale runaway
async def trigger_runaway_check() -> Dict[str, Any]:
    """Trigger manuale del check runaway protection"""
    await task_executor.periodic_runaway_check()
    return {
        "success": True,
        "message": "Runaway check completed",
        "protection_status": task_executor.get_runaway_protection_status()
    }

# NUOVO: Funzione per reset manuale di workspace pausato
async def reset_workspace_auto_generation(workspace_id: str) -> Dict[str, Any]:
    """Reset manuale dell'auto-generation per un workspace"""
    if workspace_id in task_executor.workspace_auto_generation_paused:
        await task_executor._resume_auto_generation_for_workspace(workspace_id)
        return {
            "success": True,
            "message": f"Auto-generation resumed for workspace {workspace_id}"
        }
    else:
        return {
            "success": False,
            "message": f"Auto-generation was not paused for workspace {workspace_id}"
        }