#!/usr/bin/env python3
"""
Enhanced Thinking Process Validation Script
Tests the enhanced metadata capture for agents and tools in thinking processes.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

WORKSPACE_ID = "1f1bf9cf-3c46-48ed-96f3-ec826742ee02"
API_BASE = "http://localhost:8000"

class ThinkingProcessValidator:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.validation_results = {
            "workspace_found": False,
            "processes_found": False,
            "agent_metadata_found": False,
            "tool_metadata_found": False,
            "agent_quality": {},
            "tool_quality": {},
            "overall_score": 0
        }
    
    async def validate(self):
        """Run complete validation suite"""
        console.print("\n[bold cyan]🔍 Enhanced Thinking Process Validation Report[/bold cyan]\n")
        console.print(f"[dim]Workspace ID: {WORKSPACE_ID}[/dim]")
        console.print(f"[dim]Timestamp: {datetime.now().isoformat()}[/dim]\n")
        
        # 1. Validate workspace exists
        await self.validate_workspace()
        
        # 2. Get and analyze thinking processes
        processes = await self.get_thinking_processes()
        
        if processes:
            # 3. Validate agent metadata
            await self.validate_agent_metadata(processes)
            
            # 4. Validate tool execution metadata
            await self.validate_tool_metadata(processes)
            
            # 5. Calculate overall quality score
            self.calculate_overall_score()
        
        # 6. Generate report
        self.generate_report()
        
        await self.client.aclose()
    
    async def validate_workspace(self):
        """Validate workspace exists and is active"""
        try:
            response = await self.client.get(f"{API_BASE}/api/workspaces/{WORKSPACE_ID}")
            if response.status_code == 200:
                workspace = response.json()
                self.validation_results["workspace_found"] = True
                console.print(f"✅ Workspace found: [green]{workspace['name']}[/green]")
                console.print(f"   Status: [yellow]{workspace['status']}[/yellow]")
                console.print(f"   Goal: {workspace['goal'][:100]}...")
            else:
                console.print(f"❌ Workspace not found: {response.status_code}")
        except Exception as e:
            console.print(f"❌ Error fetching workspace: {e}")
    
    async def get_thinking_processes(self) -> List[Dict]:
        """Fetch thinking processes for workspace"""
        try:
            response = await self.client.get(f"{API_BASE}/api/thinking/workspace/{WORKSPACE_ID}")
            if response.status_code == 200:
                data = response.json()
                processes = data.get("processes", [])
                if processes:
                    self.validation_results["processes_found"] = True
                    console.print(f"\n✅ Found [green]{len(processes)}[/green] thinking processes")
                    return processes
                else:
                    console.print("⚠️  No thinking processes found")
                    return []
            else:
                console.print(f"❌ Error fetching processes: {response.status_code}")
                return []
        except Exception as e:
            console.print(f"❌ Error: {e}")
            return []
    
    async def validate_agent_metadata(self, processes: List[Dict]):
        """Validate agent metadata in thinking processes"""
        console.print("\n[bold]📊 Agent Metadata Analysis[/bold]")
        
        agent_steps = []
        for process in processes:
            for step in process.get("steps", []):
                if "metadata" in step and "agent" in step.get("metadata", {}):
                    agent_steps.append(step)
        
        if not agent_steps:
            console.print("❌ No agent metadata found in any steps")
            return
        
        self.validation_results["agent_metadata_found"] = True
        console.print(f"✅ Found agent metadata in [green]{len(agent_steps)}[/green] steps")
        
        # Analyze agent metadata quality
        table = Table(title="Agent Metadata Quality")
        table.add_column("Field", style="cyan")
        table.add_column("Coverage", style="green")
        table.add_column("Quality", style="yellow")
        
        fields_to_check = ["id", "name", "role", "seniority", "skills", "status"]
        field_coverage = {field: 0 for field in fields_to_check}
        field_quality = {field: [] for field in fields_to_check}
        
        for step in agent_steps:
            agent = step["metadata"]["agent"]
            for field in fields_to_check:
                if field in agent and agent[field]:
                    field_coverage[field] += 1
                    # Check quality
                    if field == "name" and not agent[field].startswith("agent_"):
                        field_quality[field].append("realistic")
                    elif field == "seniority" and agent[field] in ["junior", "senior", "expert"]:
                        field_quality[field].append("valid")
                    elif field == "skills" and isinstance(agent[field], list):
                        field_quality[field].append("structured")
        
        for field in fields_to_check:
            coverage_pct = (field_coverage[field] / len(agent_steps)) * 100 if agent_steps else 0
            quality_score = "High" if len(field_quality[field]) > len(agent_steps) * 0.8 else "Medium" if len(field_quality[field]) > len(agent_steps) * 0.5 else "Low"
            table.add_row(field, f"{coverage_pct:.1f}%", quality_score)
            self.validation_results["agent_quality"][field] = {
                "coverage": coverage_pct,
                "quality": quality_score
            }
        
        console.print(table)
        
        # Show sample agent metadata
        if agent_steps:
            sample = agent_steps[0]["metadata"]["agent"]
            console.print("\n[dim]Sample Agent Metadata:[/dim]")
            console.print(Panel(json.dumps(sample, indent=2), title="Agent Context", border_style="blue"))
    
    async def validate_tool_metadata(self, processes: List[Dict]):
        """Validate tool execution metadata"""
        console.print("\n[bold]🔧 Tool Execution Analysis[/bold]")
        
        tool_steps = []
        for process in processes:
            for step in process.get("steps", []):
                if "metadata" in step and "tool" in step.get("metadata", {}):
                    tool_steps.append(step)
        
        if not tool_steps:
            console.print("❌ No tool metadata found in any steps")
            return
        
        self.validation_results["tool_metadata_found"] = True
        console.print(f"✅ Found tool metadata in [green]{len(tool_steps)}[/green] steps")
        
        # Analyze tool metadata quality
        table = Table(title="Tool Execution Metadata Quality")
        table.add_column("Field", style="cyan")
        table.add_column("Coverage", style="green")
        table.add_column("Quality", style="yellow")
        
        fields_to_check = ["name", "type", "success", "execution_time_ms", "parameters", "error"]
        field_coverage = {field: 0 for field in fields_to_check}
        field_quality = {field: [] for field in fields_to_check}
        
        for step in tool_steps:
            tool = step["metadata"]["tool"]
            for field in fields_to_check:
                if field in tool:
                    field_coverage[field] += 1
                    # Check quality
                    if field == "execution_time_ms" and isinstance(tool[field], (int, float)) and tool[field] > 0:
                        field_quality[field].append("valid")
                    elif field == "success" and isinstance(tool[field], bool):
                        field_quality[field].append("valid")
                    elif field == "parameters" and isinstance(tool[field], dict):
                        field_quality[field].append("structured")
        
        for field in fields_to_check:
            coverage_pct = (field_coverage[field] / len(tool_steps)) * 100 if tool_steps else 0
            quality_score = "High" if len(field_quality[field]) > len(tool_steps) * 0.8 else "Medium" if len(field_quality[field]) > len(tool_steps) * 0.5 else "Low"
            table.add_row(field, f"{coverage_pct:.1f}%", quality_score)
            self.validation_results["tool_quality"][field] = {
                "coverage": coverage_pct,
                "quality": quality_score
            }
        
        console.print(table)
        
        # Show sample tool metadata
        if tool_steps:
            sample = tool_steps[0]["metadata"]["tool"]
            console.print("\n[dim]Sample Tool Metadata:[/dim]")
            console.print(Panel(json.dumps(sample, indent=2), title="Tool Execution", border_style="green"))
            
            # Show results if available
            if "results" in tool_steps[0]["metadata"]:
                results = tool_steps[0]["metadata"]["results"]
                console.print(Panel(json.dumps(results, indent=2), title="Execution Results", border_style="yellow"))
    
    def calculate_overall_score(self):
        """Calculate overall validation score"""
        scores = []
        
        # Workspace and processes
        if self.validation_results["workspace_found"]:
            scores.append(10)
        if self.validation_results["processes_found"]:
            scores.append(10)
        
        # Agent metadata
        if self.validation_results["agent_metadata_found"]:
            scores.append(20)
            # Add quality scores
            for field, quality in self.validation_results["agent_quality"].items():
                if quality["coverage"] > 80:
                    scores.append(5)
        
        # Tool metadata
        if self.validation_results["tool_metadata_found"]:
            scores.append(20)
            # Add quality scores
            for field, quality in self.validation_results["tool_quality"].items():
                if quality["coverage"] > 80:
                    scores.append(5)
        
        self.validation_results["overall_score"] = sum(scores)
    
    def generate_report(self):
        """Generate final validation report"""
        console.print("\n" + "="*60)
        console.print("[bold]📈 Validation Summary[/bold]")
        console.print("="*60)
        
        # Overall status
        score = self.validation_results["overall_score"]
        if score >= 80:
            status = "[bold green]✅ EXCELLENT[/bold green]"
            message = "Enhanced thinking processes are fully functional with high-quality metadata!"
        elif score >= 60:
            status = "[bold yellow]⚠️  GOOD[/bold yellow]"
            message = "Enhanced thinking processes are working well with room for improvement."
        elif score >= 40:
            status = "[bold orange]⚠️  PARTIAL[/bold orange]"
            message = "Enhanced metadata is partially captured but needs improvement."
        else:
            status = "[bold red]❌ NEEDS WORK[/bold red]"
            message = "Enhanced metadata capture needs significant improvement."
        
        console.print(f"\nOverall Status: {status}")
        console.print(f"Score: [bold]{score}/100[/bold]")
        console.print(f"\n{message}")
        
        # Component status
        console.print("\n[bold]Component Status:[/bold]")
        components = [
            ("Workspace", self.validation_results["workspace_found"]),
            ("Thinking Processes", self.validation_results["processes_found"]),
            ("Agent Metadata", self.validation_results["agent_metadata_found"]),
            ("Tool Metadata", self.validation_results["tool_metadata_found"])
        ]
        
        for name, found in components:
            status = "✅" if found else "❌"
            console.print(f"  {status} {name}")
        
        # Recommendations
        console.print("\n[bold]💡 Recommendations:[/bold]")
        if not self.validation_results["processes_found"]:
            console.print("  • Trigger some tasks to generate thinking processes")
        if not self.validation_results["agent_metadata_found"]:
            console.print("  • Ensure agents are properly initialized with metadata")
        if not self.validation_results["tool_metadata_found"]:
            console.print("  • Verify tool execution tracking is enabled")
        
        if score >= 80:
            console.print("  • [green]System is working excellently! Continue monitoring.[/green]")
        
        console.print("\n" + "="*60)

async def main():
    validator = ThinkingProcessValidator()
    await validator.validate()

if __name__ == "__main__":
    asyncio.run(main())