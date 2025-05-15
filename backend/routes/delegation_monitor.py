from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from database import (
    get_workspace,
    list_agents as db_list_agents,
    list_tasks
)
from executor import task_executor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/delegation", tags=["delegation-monitor"])

@router.get("/workspace/{workspace_id}/analysis", response_model=Dict[str, Any])
async def get_delegation_analysis(workspace_id: UUID):
    """Analizza i pattern di delegazione per un workspace"""
    try:
        # Recupera dati
        tasks = await list_tasks(str(workspace_id))
        agents = await db_list_agents(str(workspace_id))
        
        # Analizza pattern di delegazione dai log dell'executor
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 100)
        
        # Separa i task per tipo
        delegation_tasks = []
        self_execution_tasks = []
        escalation_tasks = []
        
        for task in tasks:
            task_name = task.get("name", "")
            if task_name.startswith("[EXPANDED]"):
                self_execution_tasks.append(task)
            elif task_name.startswith("[ESCALATION]"):
                escalation_tasks.append(task)
            elif task_name.startswith("[FORCED]"):
                self_execution_tasks.append(task)
            elif any(event.get("task_id") == task["id"] and event.get("event") == "subtask_delegated" 
                    for event in recent_activity):
                delegation_tasks.append(task)
        
        # Analizza fallimenti di delegazione
        failed_delegations = []
        for event in recent_activity:
            if event.get("event") == "delegation_failed":
                failed_delegations.append(event)
        
        # Statistiche per ruolo
        role_stats = defaultdict(lambda: {
            "total_requests": 0,
            "successful_delegations": 0,
            "self_executions": 0,
            "escalations": 0,
            "failures": 0
        })
        
        # Popola statistiche dai task
        for task in delegation_tasks:
            # Cerca nei log chi ha delegato questo task
            for event in recent_activity:
                if (event.get("task_id") == task["id"] and 
                    event.get("event") == "subtask_delegated"):
                    details = event.get("details", {})
                    source_agent = details.get("delegated_by", "Unknown")
                    if source_agent != "Unknown":
                        role_stats[source_agent]["total_requests"] += 1
                        role_stats[source_agent]["successful_delegations"] += 1
        
        for task in self_execution_tasks:
            # Trova chi ha fatto self-execution
            agent = next((a for a in agents if a["id"] == task.get("agent_id")), None)
            if agent:
                role_stats[agent["name"]]["total_requests"] += 1
                role_stats[agent["name"]]["self_executions"] += 1
        
        for task in escalation_tasks:
            # Trova chi ha escalato
            for event in recent_activity:
                if (event.get("task_id") == task["id"] and 
                    event.get("event") == "escalation_created"):
                    details = event.get("details", {})
                    # L'escalation viene creata dall'agente che non riesce a delegare
                    # Cerca nell'evento precedente chi ha provato a delegare
                    role_stats["System"]["escalations"] += 1
        
        for event in failed_delegations:
            details = event.get("details", {})
            source_agent = details.get("agent_name", "Unknown")
            if source_agent != "Unknown":
                role_stats[source_agent]["total_requests"] += 1
                role_stats[source_agent]["failures"] += 1
        
        # Calcola delegation patterns
        delegated_roles = Counter()
        for event in recent_activity:
            if event.get("event") == "subtask_delegated":
                details = event.get("details", {})
                target_role = details.get("assigned_agent_name", "Unknown")
                delegated_roles[target_role] += 1
        
        # Trova colli di bottiglia
        bottlenecks = []
        for event in recent_activity:
            if event.get("event") == "delegation_failed":
                details = event.get("details", {})
                target_role = details.get("error_message", "")
                if "No suitable agent" in target_role:
                    # Estrai il ruolo dalla error message
                    role_match = target_role.split("'")
                    if len(role_match) >= 2:
                        missing_role = role_match[1]
                        bottlenecks.append(missing_role)
        
        bottleneck_counter = Counter(bottlenecks)
        
        # Health score del sistema di delegazione
        total_attempts = len(delegation_tasks) + len(self_execution_tasks) + len(escalation_tasks) + len(failed_delegations)
        success_rate = len(delegation_tasks) / total_attempts if total_attempts > 0 else 1.0
        self_execution_rate = len(self_execution_tasks) / total_attempts if total_attempts > 0 else 0.0
        escalation_rate = len(escalation_tasks) / total_attempts if total_attempts > 0 else 0.0
        
        health_score = (success_rate * 0.6 + (1 - escalation_rate) * 0.3 + (1 - len(failed_delegations)/max(total_attempts, 1)) * 0.1) * 100
        
        return {
            "workspace_id": str(workspace_id),
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_delegation_attempts": total_attempts,
                "successful_delegations": len(delegation_tasks),
                "self_executions": len(self_execution_tasks),
                "escalations": len(escalation_tasks),
                "failures": len(failed_delegations),
                "success_rate": round(success_rate * 100, 2),
                "self_execution_rate": round(self_execution_rate * 100, 2),
                "escalation_rate": round(escalation_rate * 100, 2),
                "health_score": round(health_score, 2)
            },
            "role_statistics": dict(role_stats),
            "most_delegated_to": dict(delegated_roles.most_common(5)),
            "bottlenecks": dict(bottleneck_counter.most_common(5)),
            "recommendations": _generate_delegation_recommendations(
                success_rate, self_execution_rate, escalation_rate, 
                bottleneck_counter, role_stats
            )
        }
        
    except Exception as e:
        logger.error(f"Error in delegation analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze delegations: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/bottlenecks", response_model=List[Dict[str, Any]])
async def get_delegation_bottlenecks(workspace_id: UUID):
    """Identifica i colli di bottiglia nella delegazione"""
    try:
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 200)
        
        # Trova pattern di fallimenti ripetuti
        failed_roles = defaultdict(list)
        for event in recent_activity:
            if event.get("event") == "delegation_failed":
                details = event.get("details", {})
                error_msg = details.get("error_message", "")
                timestamp = event.get("timestamp")
                
                # Estrai il ruolo richiesto
                if "No suitable agent for" in error_msg:
                    role_parts = error_msg.split("'")
                    if len(role_parts) >= 2:
                        role = role_parts[1]
                        failed_roles[role].append({
                            "timestamp": timestamp,
                            "source_agent": details.get("agent_name", "Unknown"),
                            "task_name": details.get("task_name", "Unknown")
                        })
        
        # Converti in lista ordinata per frequenza
        bottlenecks = []
        for role, failures in failed_roles.items():
            # Calcola se è un trend recente (ultimo giorno)
            recent_failures = [f for f in failures 
                             if datetime.fromisoformat(f["timestamp"]) > datetime.now() - timedelta(days=1)]
            
            # Conta agenti unici che hanno richiesto questo ruolo
            unique_requesters = len(set(f["source_agent"] for f in failures))
            
            bottlenecks.append({
                "missing_role": role,
                "total_failures": len(failures),
                "recent_failures": len(recent_failures),
                "unique_requesters": unique_requesters,
                "latest_failure": max(failures, key=lambda x: x["timestamp"])["timestamp"],
                "trend": "increasing" if len(recent_failures) > len(failures) / 2 else "stable",
                "severity": _calculate_bottleneck_severity(len(failures), unique_requesters, len(recent_failures)),
                "sample_requests": failures[-3:]  # Ultimi 3 per context
            })
        
        # Ordina per severità
        bottlenecks.sort(key=lambda x: x["severity"], reverse=True)
        
        return bottlenecks
        
    except Exception as e:
        logger.error(f"Error getting delegation bottlenecks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bottlenecks: {str(e)}"
        )

@router.post("/workspace/{workspace_id}/reset-cache", status_code=status.HTTP_200_OK)
async def reset_delegation_cache(workspace_id: UUID):
    """Reset del cache di delegazione per tutti gli agenti del workspace"""
    try:
        # Nota: Questa implementazione assumerebbe che gli agenti 
        # siano accessibili dall'executor. Per ora resettiamo i log
        
        # Alternative: resetta i log di delegazione recenti
        return {
            "success": True,
            "message": "Delegation cache reset requested",
            "workspace_id": str(workspace_id),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting delegation cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset cache: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/suggestions", response_model=Dict[str, Any])
async def get_team_expansion_suggestions(workspace_id: UUID):
    """Suggerimenti per espansione del team basati sui pattern di delegazione"""
    try:
        # Analizza bottlenecks
        bottlenecks = await get_delegation_bottlenecks(workspace_id)
        
        # Recupera team corrente
        agents = await db_list_agents(str(workspace_id))
        current_roles = [agent["role"] for agent in agents if agent.get("status") == "active"]
        
        suggestions = []
        
        # Suggerimenti basati sui bottlenecks
        for bottleneck in bottlenecks[:5]:  # Top 5
            if bottleneck["severity"] >= 7:  # Severità alta
                missing_role = bottleneck["missing_role"]
                
                # Suggerisci seniority basata su complessità
                suggested_seniority = "senior"
                if bottleneck["unique_requesters"] >= 3:
                    suggested_seniority = "expert"
                elif bottleneck["total_failures"] <= 2:
                    suggested_seniority = "junior"
                
                suggestions.append({
                    "type": "new_agent",
                    "role": missing_role,
                    "suggested_seniority": suggested_seniority,
                    "priority": bottleneck["severity"],
                    "reasoning": f"High demand ({bottleneck['total_failures']} failures) from {bottleneck['unique_requesters']} different agents",
                    "recent_activity": bottleneck["recent_failures"],
                    "estimated_workload": _estimate_role_workload(missing_role, bottlenecks)
                })
        
        # Suggerimenti per cross-training esistenti
        cross_training_suggestions = []
        for agent in agents:
            if agent.get("status") == "active":
                # Trova le delegazioni fallite che potrebbero essere gestite con training
                compatible_roles = _find_compatible_missing_roles(agent["role"], bottlenecks)
                if compatible_roles:
                    cross_training_suggestions.append({
                        "type": "cross_training",
                        "agent_name": agent["name"],
                        "current_role": agent["role"],
                        "suggested_additional_capabilities": compatible_roles[:2],
                        "potential_impact": len(compatible_roles)
                    })
        
        # Suggerimenti per team restructuring
        restructure_suggestions = []
        if len(suggestions) >= 3:  # Molti ruoli mancanti
            restructure_suggestions.append({
                "type": "team_restructure",
                "recommendation": "Consider creating more generalist roles",
                "reasoning": f"High fragmentation: {len(suggestions)} missing specialized roles",
                "proposed_approach": "Hybrid agents with broader capabilities"
            })
        
        return {
            "workspace_id": str(workspace_id),
            "current_team_size": len(agents),
            "active_agents": len(current_roles),
            "suggestions": {
                "new_agents": suggestions,
                "cross_training": cross_training_suggestions,
                "restructuring": restructure_suggestions
            },
            "summary": {
                "total_suggestions": len(suggestions) + len(cross_training_suggestions),
                "high_priority_additions": len([s for s in suggestions if s["priority"] >= 8]),
                "cross_training_opportunities": len(cross_training_suggestions)
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating team suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        )

# Helper functions
def _generate_delegation_recommendations(
    success_rate: float,
    self_execution_rate: float,
    escalation_rate: float,
    bottlenecks: Counter,
    role_stats: Dict
) -> List[str]:
    """Genera raccomandazioni basate sull'analisi di delegazione"""
    recommendations = []
    
    if success_rate < 0.7:
        recommendations.append(f"Low delegation success rate ({success_rate*100:.1f}%). Consider team expansion or role rebalancing.")
    
    if self_execution_rate > 0.3:
        recommendations.append(f"High self-execution rate ({self_execution_rate*100:.1f}%). Agents frequently expanding scope - may indicate missing specializations.")
    
    if escalation_rate > 0.2:
        recommendations.append(f"High escalation rate ({escalation_rate*100:.1f}%). Consider adding specialized agents for frequently requested roles.")
    
    # Top bottlenecks
    if bottlenecks:
        top_bottleneck = bottlenecks.most_common(1)[0]
        recommendations.append(f"Most requested missing role: '{top_bottleneck[0]}' ({top_bottleneck[1]} requests). Consider adding this specialist.")
    
    # Role-specific recommendations
    overworked_agents = [name for name, stats in role_stats.items() 
                        if stats["total_requests"] > 10 and stats["successful_delegations"] / stats["total_requests"] < 0.6]
    
    if overworked_agents:
        recommendations.append(f"Agents with high delegation load but low success: {', '.join(overworked_agents)}. Consider supporting roles.")
    
    if not recommendations:
        recommendations.append("Delegation system appears healthy. Continue monitoring for emerging patterns.")
    
    return recommendations

def _calculate_bottleneck_severity(total_failures: int, unique_requesters: int, recent_failures: int) -> int:
    """Calcola severity score per un bottleneck (0-10)"""
    # Componenti del severity score
    frequency_score = min(total_failures / 5, 4)  # Max 4 points
    diversity_score = min(unique_requesters / 2, 3)  # Max 3 points  
    recency_score = min(recent_failures / 2, 3)  # Max 3 points
    
    return round(frequency_score + diversity_score + recency_score)

def _estimate_role_workload(role: str, bottlenecks: List[Dict]) -> str:
    """Stima il carico di lavoro per un ruolo mancante"""
    # Trova il bottleneck per questo ruolo
    role_bottleneck = next((b for b in bottlenecks if b["missing_role"] == role), None)
    
    if not role_bottleneck:
        return "low"
    
    total_requests = role_bottleneck["total_failures"]
    recent_requests = role_bottleneck["recent_failures"]
    
    if recent_requests > 5:
        return "high"
    elif recent_requests > 2 or total_requests > 8:
        return "medium"
    else:
        return "low"

def _find_compatible_missing_roles(current_role: str, bottlenecks: List[Dict]) -> List[str]:
    """Trova ruoli mancanti che potrebbero essere compatibili con un ruolo esistente"""
    current_lower = current_role.lower()
    compatible = []
    
    for bottleneck in bottlenecks:
        missing_role = bottleneck["missing_role"].lower()
        
        # Controlli di compatibilità
        # 1. Overlap di parole chiave
        current_words = set(current_lower.split())
        missing_words = set(missing_role.split())
        if len(current_words & missing_words) >= 1:
            compatible.append(bottleneck["missing_role"])
            continue
        
        # 2. Compatibilità semantica
        if "analyst" in current_lower and "analys" in missing_role:
            compatible.append(bottleneck["missing_role"])
        elif "manager" in current_lower and any(word in missing_role for word in ["manage", "coord", "lead"]):
            compatible.append(bottleneck["missing_role"])
        elif "specialist" in current_lower and "specialist" in missing_role:
            compatible.append(bottleneck["missing_role"])
    
    return compatible