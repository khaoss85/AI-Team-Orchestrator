#!/usr/bin/env python3
"""
🚨 CRITICAL COST IMPACT ANALYZER
Calculates financial impact of current polling patterns and resource leaks
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any

class CostImpactAnalyzer:
    """Analyzes cost impact of current system inefficiencies"""
    
    def __init__(self):
        # OpenAI Pricing (GPT-4 Turbo as reference)
        self.openai_costs = {
            "gpt-4-turbo-input": 0.01 / 1000,  # $0.01 per 1K tokens
            "gpt-4-turbo-output": 0.03 / 1000,  # $0.03 per 1K tokens
            "average_request_tokens": 2000,  # Average tokens per goals/preview request
        }
        
        # Supabase Pricing (Pro plan)
        self.supabase_costs = {
            "api_request": 0.000002,  # $2 per million requests
            "bandwidth_gb": 0.09,  # $0.09 per GB
            "average_request_kb": 2,  # Average KB per request
        }
        
        # WebSocket costs
        self.websocket_costs = {
            "connection_hour": 0.0001,  # Estimated connection cost per hour
            "message_cost": 0.000001,  # Cost per message
        }
        
    def calculate_polling_storm_cost(self) -> Dict[str, Any]:
        """Calculate cost of frontend polling every 3 seconds"""
        
        # Polling pattern: /goals/progress every 3 seconds
        polls_per_hour = 3600 / 3  # 1200 requests/hour
        polls_per_day = polls_per_hour * 24  # 28,800 requests/day
        polls_per_month = polls_per_day * 30  # 864,000 requests/month
        
        # Cost calculation
        api_cost_per_month = polls_per_month * self.supabase_costs["api_request"]
        bandwidth_gb_month = (polls_per_month * self.supabase_costs["average_request_kb"]) / (1024 * 1024)
        bandwidth_cost_month = bandwidth_gb_month * self.supabase_costs["bandwidth_gb"]
        
        # Per workspace costs
        active_workspaces_estimate = 10  # Conservative estimate
        total_monthly_polling_cost = (api_cost_per_month + bandwidth_cost_month) * active_workspaces_estimate
        
        return {
            "pattern": "Frontend polling /goals/progress every 3 seconds",
            "frequency": {
                "polls_per_hour": polls_per_hour,
                "polls_per_day": polls_per_day,
                "polls_per_month": polls_per_month
            },
            "cost_breakdown": {
                "api_cost_per_workspace_month": f"${api_cost_per_month:.2f}",
                "bandwidth_cost_per_workspace_month": f"${bandwidth_cost_month:.2f}",
                "total_per_workspace_month": f"${api_cost_per_month + bandwidth_cost_month:.2f}"
            },
            "estimated_total_monthly_cost": f"${total_monthly_polling_cost:.2f}",
            "annual_projection": f"${total_monthly_polling_cost * 12:.2f}",
            "optimization_potential": {
                "use_websocket_updates": "Reduce to 0 polling requests",
                "increase_interval_to_30s": f"${total_monthly_polling_cost * 0.1:.2f}/month",
                "smart_polling_on_activity": f"${total_monthly_polling_cost * 0.05:.2f}/month"
            }
        }
    
    def calculate_expensive_workflow_cost(self) -> Dict[str, Any]:
        """Calculate cost of expensive goals/preview workflow (27+ seconds)"""
        
        # Assumptions based on logs
        preview_calls_per_day = 50  # Conservative estimate
        tokens_per_call = 3000  # Based on complex goal extraction
        database_calls_per_preview = 8  # From log analysis
        
        # OpenAI costs
        openai_input_cost = (tokens_per_call * 0.7) * self.openai_costs["gpt-4-turbo-input"]
        openai_output_cost = (tokens_per_call * 0.3) * self.openai_costs["gpt-4-turbo-output"]
        openai_cost_per_call = openai_input_cost + openai_output_cost
        
        # Database costs
        db_cost_per_call = database_calls_per_preview * self.supabase_costs["api_request"]
        
        # Total costs
        total_cost_per_call = openai_cost_per_call + db_cost_per_call
        daily_cost = total_cost_per_call * preview_calls_per_day
        monthly_cost = daily_cost * 30
        
        # Time cost (opportunity cost)
        average_wait_time_seconds = 27
        total_wait_hours_per_month = (preview_calls_per_day * 30 * average_wait_time_seconds) / 3600
        productivity_cost = total_wait_hours_per_month * 50  # $50/hour productivity value
        
        return {
            "pattern": "Goals/preview endpoint taking 27+ seconds",
            "performance": {
                "average_response_time": "27 seconds",
                "database_calls": database_calls_per_preview,
                "tokens_processed": tokens_per_call
            },
            "cost_breakdown": {
                "openai_cost_per_call": f"${openai_cost_per_call:.4f}",
                "database_cost_per_call": f"${db_cost_per_call:.6f}",
                "total_cost_per_call": f"${total_cost_per_call:.4f}"
            },
            "monthly_costs": {
                "direct_api_costs": f"${monthly_cost:.2f}",
                "productivity_loss": f"${productivity_cost:.2f}",
                "total_monthly_impact": f"${monthly_cost + productivity_cost:.2f}"
            },
            "optimization_potential": {
                "cache_workspace_context": "Save 6 DB calls per request",
                "batch_database_queries": "Reduce to 2 DB calls total",
                "implement_streaming_response": "Reduce perceived wait to <5 seconds",
                "estimated_savings": f"${(monthly_cost * 0.7):.2f}/month"
            }
        }
    
    def calculate_websocket_leak_cost(self) -> Dict[str, Any]:
        """Calculate cost of WebSocket connection leaks"""
        
        # From logs: multiple simultaneous connections per workspace
        leaked_connections_per_workspace = 3  # Average from logs
        active_workspaces = 10
        total_leaked_connections = leaked_connections_per_workspace * active_workspaces
        
        # Cost calculation
        connection_hours_per_month = total_leaked_connections * 24 * 30
        connection_cost = connection_hours_per_month * self.websocket_costs["connection_hour"]
        
        # Memory/resource impact
        memory_per_connection_mb = 2  # Estimated
        total_memory_leaked_gb = (total_leaked_connections * memory_per_connection_mb) / 1024
        memory_cost = total_memory_leaked_gb * 5  # $5/GB-month for cloud memory
        
        return {
            "pattern": "Multiple WebSocket connections opening simultaneously",
            "leaks": {
                "connections_per_workspace": leaked_connections_per_workspace,
                "total_leaked_connections": total_leaked_connections,
                "connection_hours_per_month": connection_hours_per_month
            },
            "cost_breakdown": {
                "connection_costs": f"${connection_cost:.2f}",
                "memory_costs": f"${memory_cost:.2f}",
                "total_monthly_cost": f"${connection_cost + memory_cost:.2f}"
            },
            "optimization_potential": {
                "implement_connection_reuse": "Single connection per workspace",
                "add_connection_cleanup": "Automatic cleanup after 30min idle",
                "estimated_savings": f"${(connection_cost + memory_cost) * 0.66:.2f}/month"
            }
        }
    
    def generate_total_impact_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost impact report"""
        
        polling_impact = self.calculate_polling_storm_cost()
        workflow_impact = self.calculate_expensive_workflow_cost()
        websocket_impact = self.calculate_websocket_leak_cost()
        
        # Extract monthly costs
        polling_cost = float(polling_impact["estimated_total_monthly_cost"].replace("$", ""))
        workflow_cost = float(workflow_impact["monthly_costs"]["total_monthly_impact"].replace("$", ""))
        websocket_cost = float(websocket_impact["cost_breakdown"]["total_monthly_cost"].replace("$", ""))
        
        total_monthly_waste = polling_cost + workflow_cost + websocket_cost
        
        # Priority scoring (1-10)
        issues = [
            {
                "issue": "Polling Storm",
                "monthly_cost": polling_cost,
                "fix_effort": 3,  # Low effort
                "priority_score": 9,  # High priority
                "quick_fix": "Increase polling interval to 30 seconds"
            },
            {
                "issue": "Expensive Workflow",
                "monthly_cost": workflow_cost,
                "fix_effort": 6,  # Medium effort
                "priority_score": 8,
                "quick_fix": "Cache workspace context for 5 minutes"
            },
            {
                "issue": "WebSocket Leaks",
                "monthly_cost": websocket_cost,
                "fix_effort": 4,  # Low-medium effort
                "priority_score": 7,
                "quick_fix": "Implement connection singleton pattern"
            }
        ]
        
        return {
            "executive_summary": {
                "total_monthly_waste": f"${total_monthly_waste:.2f}",
                "annual_waste_projection": f"${total_monthly_waste * 12:.2f}",
                "potential_savings_with_quick_fixes": f"${total_monthly_waste * 0.6:.2f}/month",
                "potential_savings_with_full_optimization": f"${total_monthly_waste * 0.85:.2f}/month"
            },
            "critical_issues": issues,
            "detailed_analysis": {
                "polling_storm": polling_impact,
                "expensive_workflow": workflow_impact,
                "websocket_leaks": websocket_impact
            },
            "recommended_immediate_actions": [
                {
                    "action": "🔴 URGENT: Increase polling interval from 3s to 30s",
                    "implementation": "Update useGoalPreview.ts line 288",
                    "estimated_time": "5 minutes",
                    "monthly_savings": f"${polling_cost * 0.9:.2f}"
                },
                {
                    "action": "🟠 HIGH: Cache workspace context in Redis",
                    "implementation": "Add caching layer in _get_workspace_context()",
                    "estimated_time": "2 hours",
                    "monthly_savings": f"${workflow_cost * 0.5:.2f}"
                },
                {
                    "action": "🟡 MEDIUM: Fix WebSocket connection management",
                    "implementation": "Implement singleton pattern in websocket manager",
                    "estimated_time": "1 hour",
                    "monthly_savings": f"${websocket_cost * 0.66:.2f}"
                }
            ],
            "monitoring_implementation": {
                "metrics_to_track": [
                    "API calls per minute by endpoint",
                    "Average response time by endpoint",
                    "Active WebSocket connections",
                    "Cache hit rates",
                    "OpenAI token usage per request"
                ],
                "alerting_thresholds": {
                    "polling_rate": "Alert if > 20 req/min from single client",
                    "response_time": "Alert if > 10 seconds for any endpoint",
                    "websocket_connections": "Alert if > 2 connections per workspace",
                    "daily_cost": "Alert if daily costs exceed $50"
                }
            },
            "generated_at": datetime.now().isoformat(),
            "workspace_analyzed": "e29a33af-b473-4d9c-b983-f5c1aa70a830"
        }

def main():
    """Generate and display cost impact analysis"""
    analyzer = CostImpactAnalyzer()
    report = analyzer.generate_total_impact_report()
    
    # Save report
    with open("/Users/pelleri/Documents/ai-team-orchestrator/backend/cost_impact_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("🚨 CRITICAL COST IMPACT ANALYSIS")
    print("="*60)
    print(f"\n💸 TOTAL MONTHLY WASTE: {report['executive_summary']['total_monthly_waste']}")
    print(f"📈 ANNUAL PROJECTION: {report['executive_summary']['annual_waste_projection']}")
    print(f"💰 QUICK FIX SAVINGS: {report['executive_summary']['potential_savings_with_quick_fixes']}/month")
    print("\n🔥 TOP PRIORITY FIXES:")
    for action in report['recommended_immediate_actions']:
        print(f"\n{action['action']}")
        print(f"  ⏱️  Time: {action['estimated_time']}")
        print(f"  💵 Saves: {action['monthly_savings']}/month")
    print("\n" + "="*60)
    print("📊 Full report saved to: cost_impact_report.json")
    print("="*60 + "\n")
    
    return report

if __name__ == "__main__":
    main()