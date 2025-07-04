#!/usr/bin/env python3
"""
📊 LOG ANALYSIS AUDIT SCRIPT  
================================================================================
Analizza log per trace ID, duplicazioni eventi, consistenza stato
TODO: Aggiornare LOG_PATHS con percorsi reali dei log
"""

import re
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import hashlib

class LogAuditAnalyzer:
    """Analyzer per audit dei log di sistema"""
    
    def __init__(self):
        # TODO: Sostituire con percorsi reali dei log
        self.log_paths = {
            "application": "/var/log/ai-orchestrator/app.log",
            "api": "/var/log/ai-orchestrator/api.log", 
            "database": "/var/log/ai-orchestrator/db.log",
            "orchestrator": "/var/log/ai-orchestrator/orchestrator.log",
            "audit": "./audit_*.log"  # Log di audit locale
        }
        
        self.trace_patterns = {
            "trace_id": r"trace[-_]id[:\s]*([a-zA-Z0-9\-]+)",
            "workspace_id": r"workspace[-_]id[:\s]*([a-zA-Z0-9\-]+)",
            "goal_id": r"goal[-_]id[:\s]*([a-zA-Z0-9\-]+)", 
            "task_id": r"task[-_]id[:\s]*([a-zA-Z0-9\-]+)",
            "agent_id": r"agent[-_]id[:\s]*([a-zA-Z0-9\-]+)"
        }
        
        self.event_patterns = {
            "workspace_created": r"workspace.*(created|established)",
            "goal_created": r"goal.*(created|defined)",
            "task_generated": r"task.*(generated|created)",
            "task_completed": r"task.*(completed|finished)",
            "asset_created": r"asset.*(created|generated)",
            "deliverable_ready": r"deliverable.*(ready|completed)"
        }
        
        self.findings = []
        self.trace_map = defaultdict(list)
        self.event_timeline = []
        self.duplicates_detected = []
    
    def analyze_logs_for_trace(self, trace_id: str) -> Dict[str, Any]:
        """Analizza log per un trace ID specifico"""
        print(f"🔍 Analyzing logs for trace ID: {trace_id}")
        
        analysis_result = {
            "trace_id": trace_id,
            "events_found": [],
            "component_coverage": set(),
            "timeline": [],
            "integrity_issues": [],
            "duplicate_events": []
        }
        
        # Scan tutti i log files
        for component, log_path in self.log_paths.items():
            try:
                events = self._scan_log_file(log_path, trace_id)
                analysis_result["events_found"].extend(events)
                if events:
                    analysis_result["component_coverage"].add(component)
                    
            except FileNotFoundError:
                print(f"⚠️ Log file not found: {log_path}")
                continue
            except Exception as e:
                print(f"❌ Error reading {log_path}: {e}")
                continue
        
        # Costruisci timeline
        analysis_result["timeline"] = self._build_event_timeline(analysis_result["events_found"])
        
        # Rileva duplicazioni
        analysis_result["duplicate_events"] = self._detect_duplicate_events(analysis_result["events_found"])
        
        # Verifica integrità del flusso
        analysis_result["integrity_issues"] = self._verify_flow_integrity(analysis_result["timeline"])
        
        return analysis_result
    
    def _scan_log_file(self, log_path: str, trace_id: str) -> List[Dict[str, Any]]:
        """Scansiona un file di log per eventi correlati al trace ID"""
        events = []
        
        try:
            with open(log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    # Cerca trace ID nella linea
                    if trace_id in line:
                        event = self._parse_log_line(line, line_num, log_path)
                        if event:
                            events.append(event)
                            
        except FileNotFoundError:
            # File non esiste - normale per alcuni componenti
            pass
        except Exception as e:
            print(f"❌ Error scanning {log_path}: {e}")
        
        return events
    
    def _parse_log_line(self, line: str, line_num: int, log_path: str) -> Optional[Dict[str, Any]]:
        """Parse di una linea di log per estrarre informazioni evento"""
        
        # Estrai timestamp (formati comuni)
        timestamp_patterns = [
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",  # ISO format
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",   # Standard format
            r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})"    # US format
        ]
        
        timestamp = None
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp = match.group(1)
                break
        
        # Estrai livello log
        level_match = re.search(r"\[(ERROR|WARN|INFO|DEBUG)\]", line)
        level = level_match.group(1) if level_match else "UNKNOWN"
        
        # Estrai tutti gli ID correlati
        extracted_ids = {}
        for id_type, pattern in self.trace_patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted_ids[id_type] = match.group(1)
        
        # Identifica tipo di evento
        event_type = "unknown"
        for event_name, pattern in self.event_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                event_type = event_name
                break
        
        # Calcola hash del contenuto per rilevare duplicati
        content_hash = hashlib.md5(line.strip().encode()).hexdigest()[:12]
        
        return {
            "timestamp": timestamp,
            "level": level,
            "event_type": event_type,
            "extracted_ids": extracted_ids,
            "content_hash": content_hash,
            "line_number": line_num,
            "log_file": log_path,
            "raw_line": line.strip()
        }
    
    def _build_event_timeline(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Costruisce timeline ordinata degli eventi"""
        
        # Filtra eventi con timestamp validi
        valid_events = [e for e in events if e.get("timestamp")]
        
        # Ordina per timestamp  
        try:
            valid_events.sort(key=lambda x: datetime.fromisoformat(x["timestamp"].replace(" ", "T")))
        except:
            # Fallback: ordina per line number se timestamp parsing fallisce
            valid_events.sort(key=lambda x: (x["log_file"], x["line_number"]))
        
        return valid_events
    
    def _detect_duplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rileva eventi duplicati basandosi su hash del contenuto"""
        
        hash_counter = Counter(e["content_hash"] for e in events)
        duplicates = []
        
        for content_hash, count in hash_counter.items():
            if count > 1:
                duplicate_events = [e for e in events if e["content_hash"] == content_hash]
                duplicates.append({
                    "content_hash": content_hash,
                    "duplicate_count": count,
                    "events": duplicate_events
                })
        
        return duplicates
    
    def _verify_flow_integrity(self, timeline: List[Dict[str, Any]]) -> List[str]:
        """Verifica integrità del flusso attraverso la timeline"""
        
        integrity_issues = []
        
        # Verifica sequenza logica degli eventi
        expected_sequence = [
            "workspace_created",
            "goal_created", 
            "task_generated",
            "task_completed",
            "asset_created",
            "deliverable_ready"
        ]
        
        event_types_found = [e["event_type"] for e in timeline]
        
        # Check per eventi mancanti nella sequenza
        for i, expected_event in enumerate(expected_sequence):
            if expected_event not in event_types_found:
                # Non tutti gli eventi sono sempre presenti, ma alcuni sono critici
                if expected_event in ["workspace_created", "goal_created"]:
                    integrity_issues.append(f"Critical event missing: {expected_event}")
        
        # Check per eventi fuori sequenza
        last_sequence_index = -1
        for event_type in event_types_found:
            if event_type in expected_sequence:
                current_index = expected_sequence.index(event_type)
                if current_index < last_sequence_index:
                    integrity_issues.append(f"Event out of sequence: {event_type}")
                last_sequence_index = max(last_sequence_index, current_index)
        
        # Check per gap temporali anomali
        if len(timeline) > 1:
            for i in range(1, len(timeline)):
                try:
                    prev_time = datetime.fromisoformat(timeline[i-1]["timestamp"].replace(" ", "T"))
                    curr_time = datetime.fromisoformat(timeline[i]["timestamp"].replace(" ", "T"))
                    
                    time_gap = (curr_time - prev_time).total_seconds()
                    
                    # Gap > 1 ora potrebbe indicare problemi
                    if time_gap > 3600:
                        integrity_issues.append(f"Large time gap detected: {time_gap}s between events")
                        
                except:
                    # Skip timestamp parsing errors
                    pass
        
        return integrity_issues
    
    def generate_audit_script(self, trace_id: str) -> str:
        """Genera script bash per audit automatizzato dei log"""
        
        script = f"""#!/bin/bash
# ====================================================================
# LOG AUDIT SCRIPT FOR TRACE ID: {trace_id}
# ====================================================================
# Auto-generated script per audit log con trace ID specifico
# TODO: Aggiornare LOG_PATHS con percorsi reali

set -e

TRACE_ID="{trace_id}"
AUDIT_OUTPUT="log_audit_${{TRACE_ID}}_$(date +%Y%m%d_%H%M%S).txt"

echo "🔍 Starting log audit for trace ID: $TRACE_ID" | tee "$AUDIT_OUTPUT"
echo "=====================================================================" | tee -a "$AUDIT_OUTPUT"

# TODO: Sostituire con percorsi reali dei log
LOG_PATHS=(
    "/var/log/ai-orchestrator/app.log"
    "/var/log/ai-orchestrator/api.log" 
    "/var/log/ai-orchestrator/db.log"
    "/var/log/ai-orchestrator/orchestrator.log"
    "./audit_*.log"
)

# Funzione per scan di un file log
scan_log_file() {{
    local log_file="$1"
    local trace_id="$2"
    
    if [[ -f "$log_file" ]]; then
        echo "📄 Scanning: $log_file" | tee -a "$AUDIT_OUTPUT"
        
        # Estrai linee con trace ID
        grep -n "$trace_id" "$log_file" | head -20 | tee -a "$AUDIT_OUTPUT"
        
        # Conta occorrenze
        local count=$(grep -c "$trace_id" "$log_file" || echo "0")
        echo "   Found $count occurrences" | tee -a "$AUDIT_OUTPUT"
        echo "" | tee -a "$AUDIT_OUTPUT"
    else
        echo "⚠️ Log file not found: $log_file" | tee -a "$AUDIT_OUTPUT"
    fi
}}

# Scan tutti i log files
for log_path in "${{LOG_PATHS[@]}}"; do
    scan_log_file "$log_path" "$TRACE_ID"
done

# Cerca pattern di eventi correlati
echo "🔍 Searching for related event patterns..." | tee -a "$AUDIT_OUTPUT"
echo "=====================================================================" | tee -a "$AUDIT_OUTPUT"

EVENT_PATTERNS=(
    "workspace.*created"
    "goal.*created"
    "task.*generated"
    "task.*completed" 
    "asset.*created"
    "deliverable.*ready"
)

for pattern in "${{EVENT_PATTERNS[@]}}"; do
    echo "Pattern: $pattern" | tee -a "$AUDIT_OUTPUT"
    for log_path in "${{LOG_PATHS[@]}}"; do
        if [[ -f "$log_path" ]]; then
            grep -i "$pattern" "$log_path" | grep -i "$TRACE_ID" | head -5 | tee -a "$AUDIT_OUTPUT"
        fi
    done
    echo "" | tee -a "$AUDIT_OUTPUT"
done

# Controlla duplicazioni
echo "🔍 Checking for duplicate events..." | tee -a "$AUDIT_OUTPUT"
echo "=====================================================================" | tee -a "$AUDIT_OUTPUT"

# Estrai eventi con timestamp e calcola hash
for log_path in "${{LOG_PATHS[@]}}"; do
    if [[ -f "$log_path" ]]; then
        echo "Duplicate check for: $log_path" | tee -a "$AUDIT_OUTPUT"
        grep "$TRACE_ID" "$log_path" | \\
        awk '{{print $0}}' | \\
        sort | \\
        uniq -c | \\
        awk '$1 > 1 {{print "DUPLICATE:", $0}}' | tee -a "$AUDIT_OUTPUT"
        echo "" | tee -a "$AUDIT_OUTPUT"
    fi
done

# Genera summary
echo "📊 AUDIT SUMMARY" | tee -a "$AUDIT_OUTPUT"
echo "=====================================================================" | tee -a "$AUDIT_OUTPUT"
echo "Trace ID: $TRACE_ID" | tee -a "$AUDIT_OUTPUT"
echo "Audit completed: $(date)" | tee -a "$AUDIT_OUTPUT"
echo "Report saved: $AUDIT_OUTPUT" | tee -a "$AUDIT_OUTPUT"

echo "✅ Log audit completed. Report: $AUDIT_OUTPUT"
"""
        
        return script
    
    def run_comprehensive_log_audit(self, trace_ids: List[str] = None) -> Dict[str, Any]:
        """Esegue audit completo dei log"""
        
        print("📊 COMPREHENSIVE LOG AUDIT")
        print("=" * 60)
        
        audit_results = {
            "audit_timestamp": datetime.now().isoformat(),
            "trace_analyses": {},
            "global_findings": [],
            "component_health": {},
            "recommendations": []
        }
        
        # Se non forniti trace ID, cerca pattern comuni
        if not trace_ids:
            trace_ids = self._discover_trace_ids()
        
        # Analizza ogni trace ID
        for trace_id in trace_ids:
            print(f"\\n🔍 Analyzing trace: {trace_id}")
            analysis = self.analyze_logs_for_trace(trace_id)
            audit_results["trace_analyses"][trace_id] = analysis
            
            # Aggiungi findings globali
            if analysis["integrity_issues"]:
                audit_results["global_findings"].extend(analysis["integrity_issues"])
            
            if analysis["duplicate_events"]:
                audit_results["global_findings"].append(f"Duplicates found for {trace_id}")
        
        # Analisi salute componenti
        for component in self.log_paths.keys():
            try:
                health = self._analyze_component_health(component)
                audit_results["component_health"][component] = health
            except Exception as e:
                audit_results["component_health"][component] = {"error": str(e)}
        
        # Genera raccomandazioni
        audit_results["recommendations"] = self._generate_recommendations(audit_results)
        
        return audit_results
    
    def _discover_trace_ids(self) -> List[str]:
        """Scopre trace ID dai log recenti"""
        
        discovered_traces = set()
        
        # Cerca in audit log locali per trace ID
        try:
            import glob
            audit_files = glob.glob("./audit_*.log")
            
            for audit_file in audit_files:
                with open(audit_file, 'r') as f:
                    content = f.read()
                    
                    # Cerca pattern trace ID
                    matches = re.findall(r"trace[-_]id[:\s]*([a-zA-Z0-9\-]+)", content, re.IGNORECASE)
                    discovered_traces.update(matches)
                    
        except Exception as e:
            print(f"⚠️ Error discovering trace IDs: {e}")
        
        # Fallback: usa trace ID di esempio
        if not discovered_traces:
            discovered_traces.add("audit-example-trace")
        
        return list(discovered_traces)[:5]  # Limita a 5 per performance
    
    def _analyze_component_health(self, component: str) -> Dict[str, Any]:
        """Analizza salute di un componente dai suoi log"""
        
        log_path = self.log_paths.get(component)
        if not log_path:
            return {"status": "unknown", "reason": "no_log_path"}
        
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                
                if not lines:
                    return {"status": "inactive", "reason": "empty_log"}
                
                # Analizza ultimi eventi
                recent_lines = lines[-100:]  # Ultimi 100 eventi
                
                error_count = sum(1 for line in recent_lines if "ERROR" in line)
                warn_count = sum(1 for line in recent_lines if "WARN" in line)
                
                # Determina stato salute
                if error_count > 10:
                    status = "unhealthy"
                elif warn_count > 20:
                    status = "degraded"
                else:
                    status = "healthy"
                
                return {
                    "status": status,
                    "recent_errors": error_count,
                    "recent_warnings": warn_count,
                    "total_lines": len(lines)
                }
                
        except FileNotFoundError:
            return {"status": "missing", "reason": "log_file_not_found"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    def _generate_recommendations(self, audit_results: Dict[str, Any]) -> List[str]:
        """Genera raccomandazioni basate sui risultati audit"""
        
        recommendations = []
        
        # Check per problemi globali
        if audit_results["global_findings"]:
            recommendations.append("🚨 URGENT: Address integrity issues found in trace analysis")
        
        # Check per salute componenti
        unhealthy_components = [
            comp for comp, health in audit_results["component_health"].items()
            if health.get("status") in ["unhealthy", "missing"]
        ]
        
        if unhealthy_components:
            recommendations.append(f"⚠️ Monitor unhealthy components: {', '.join(unhealthy_components)}")
        
        # Check per trace coverage
        trace_count = len(audit_results["trace_analyses"])
        if trace_count == 0:
            recommendations.append("🔍 No trace IDs found - improve trace logging")
        elif trace_count < 3:
            recommendations.append("📊 Limited trace data - consider increasing audit scope")
        
        # Fallback recommendation
        if not recommendations:
            recommendations.append("✅ System logs appear healthy - continue monitoring")
        
        return recommendations

def main():
    """Esegue audit log completo"""
    
    analyzer = LogAuditAnalyzer()
    
    # Esegui audit completo
    results = analyzer.run_comprehensive_log_audit()
    
    # Display risultati
    print("\\n📊 LOG AUDIT RESULTS")
    print("=" * 60)
    
    print(f"Traces analyzed: {len(results['trace_analyses'])}")
    print(f"Global findings: {len(results['global_findings'])}")
    print(f"Components checked: {len(results['component_health'])}")
    
    # Mostra raccomandazioni
    print("\\n💡 RECOMMENDATIONS:")
    for rec in results["recommendations"]:
        print(f"   {rec}")
    
    # Salva risultati
    output_file = f"log_audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\\n📄 Results saved: {output_file}")
    
    return len(results["global_findings"]) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)