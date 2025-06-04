# backend/utils/output_length_manager.py
"""
Manager per gestire output lunghi degli agent e prevenire troncamenti
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class OutputLengthManager:
    """Manager per gestire e ottimizzare output lunghi degli agent"""
    
    def __init__(self):
        # Limiti configurabili
        self.max_total_output_length = 50000  # 50K caratteri
        self.max_detailed_json_length = 30000  # 30K per detailed_results_json
        self.max_summary_length = 2000        # 2K per summary
        self.max_array_items = 100            # Max elementi in array
        
        # Statistiche
        self.processing_stats = {
            "total_processed": 0,
            "truncated_outputs": 0,
            "optimized_outputs": 0,
            "error_outputs": 0
        }
    
    def optimize_task_output(
        self, 
        task_output: Dict[str, Any], 
        task_id: Optional[str] = None
    ) -> tuple[Dict[str, Any], bool, List[str]]:
        """
        Ottimizza output di task per prevenire problemi di lunghezza
        
        Returns:
            tuple[optimized_output, was_modified, modifications_applied]
        """
        self.processing_stats["total_processed"] += 1
        
        modifications = []
        was_modified = False
        optimized = task_output.copy()
        
        try:
            # 1. Ottimizza summary
            if "summary" in optimized:
                new_summary, summary_modified = self._optimize_summary(
                    optimized["summary"], task_id
                )
                if summary_modified:
                    optimized["summary"] = new_summary
                    modifications.append("summary_truncated")
                    was_modified = True
            
            # 2. Ottimizza detailed_results_json
            if "detailed_results_json" in optimized:
                new_detailed, detailed_modified = self._optimize_detailed_results(
                    optimized["detailed_results_json"], task_id
                )
                if detailed_modified:
                    optimized["detailed_results_json"] = new_detailed
                    modifications.append("detailed_results_optimized")
                    was_modified = True
            
            # 3. Ottimizza array fields
            array_fields = ["next_steps", "suggestions", "recommendations"]
            for field in array_fields:
                if field in optimized and isinstance(optimized[field], list):
                    new_array, array_modified = self._optimize_array_field(
                        optimized[field], field, task_id
                    )
                    if array_modified:
                        optimized[field] = new_array
                        modifications.append(f"{field}_truncated")
                        was_modified = True
            
            # 4. Verifica lunghezza totale finale
            total_length = len(json.dumps(optimized, default=str))
            if total_length > self.max_total_output_length:
                optimized, length_modified = self._emergency_truncate(
                    optimized, task_id
                )
                if length_modified:
                    modifications.append("emergency_truncation")
                    was_modified = True
            
            # Update stats
            if was_modified:
                if "emergency_truncation" in modifications:
                    self.processing_stats["truncated_outputs"] += 1
                else:
                    self.processing_stats["optimized_outputs"] += 1
            
            return optimized, was_modified, modifications
            
        except Exception as e:
            self.processing_stats["error_outputs"] += 1
            logger.error(f"Error optimizing task output for {task_id}: {e}")
            return task_output, False, ["optimization_error"]
    
    def _optimize_summary(self, summary: str, task_id: Optional[str]) -> tuple[str, bool]:
        """Ottimizza campo summary"""
        if not isinstance(summary, str):
            return str(summary)[:self.max_summary_length], True
        
        if len(summary) <= self.max_summary_length:
            return summary, False
        
        # Truncate intelligentemente
        truncated = summary[:self.max_summary_length - 50]
        
        # Cerca l'ultimo punto o fine frase
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > self.max_summary_length * 0.7:  # Se almeno 70% è preserved
            truncated = truncated[:last_sentence_end + 1]
        
        truncated += " [Summary truncated for length]"
        
        logger.info(f"Task {task_id}: Summary truncated from {len(summary)} to {len(truncated)} chars")
        return truncated, True
    
    def _optimize_detailed_results(
        self, 
        detailed_results: str, 
        task_id: Optional[str]
    ) -> tuple[str, bool]:
        """Ottimizza detailed_results_json"""
        
        if not isinstance(detailed_results, str):
            return json.dumps({"error": "invalid_detailed_results_type"})[:1000], True
        
        if len(detailed_results) <= self.max_detailed_json_length:
            return detailed_results, False
        
        try:
            # Prova a parsare come JSON per ottimizzazione intelligente
            data = json.loads(detailed_results)
            optimized_data = self._optimize_json_data(data, task_id)
            optimized_json = json.dumps(optimized_data, separators=(',', ':'))
            
            # Se ancora troppo lungo, truncate con metadata
            if len(optimized_json) > self.max_detailed_json_length:
                truncated_data = self._truncate_json_data(optimized_data, task_id)
                optimized_json = json.dumps(truncated_data, separators=(',', ':'))
            
            logger.info(f"Task {task_id}: Detailed results optimized from {len(detailed_results)} to {len(optimized_json)} chars")
            return optimized_json, True
            
        except json.JSONDecodeError:
            # Se non è JSON valido, truncate come stringa
            truncated = detailed_results[:self.max_detailed_json_length - 100]
            truncated += '... [Content truncated - was not valid JSON]'
            logger.warning(f"Task {task_id}: Detailed results truncated as string (invalid JSON)")
            return truncated, True
    
    def _optimize_json_data(self, data: Any, task_id: Optional[str]) -> Any:
        """Ottimizza dati JSON ricorsivamente"""
        
        if isinstance(data, dict):
            optimized = {}
            for key, value in data.items():
                optimized[key] = self._optimize_json_data(value, task_id)
            return optimized
        
        elif isinstance(data, list):
            # Limita numero elementi in array
            if len(data) > self.max_array_items:
                optimized = data[:self.max_array_items]
                optimized.append(f"... [{len(data) - self.max_array_items} more items truncated]")
                return optimized
            else:
                return [self._optimize_json_data(item, task_id) for item in data]
        
        elif isinstance(data, str):
            # Limita lunghezza stringhe individuali
            max_string_length = 5000
            if len(data) > max_string_length:
                return data[:max_string_length - 20] + "... [truncated]"
            return data
        
        else:
            return data
    
    def _truncate_json_data(self, data: Dict[str, Any], task_id: Optional[str]) -> Dict[str, Any]:
        """Truncate aggressivo di dati JSON mantenendo struttura essenziale"""
        
        # Campi essenziali da preservare sempre
        essential_fields = [
            "task_id", "status", "summary", "error", "timestamp",
            "executive_summary", "key_findings", "main_results"
        ]
        
        truncated = {}
        
        # Preserva campi essenziali
        for field in essential_fields:
            if field in data:
                truncated[field] = data[field]
        
        # Aggiungi metadata di truncation
        truncated["_metadata"] = {
            "truncated": True,
            "original_fields_count": len(data),
            "truncated_fields": [k for k in data.keys() if k not in essential_fields],
            "truncation_timestamp": datetime.now().isoformat(),
            "reason": "detailed_results_too_long"
        }
        
        logger.warning(f"Task {task_id}: Applied aggressive JSON truncation")
        return truncated
    
    def _optimize_array_field(
        self, 
        array_data: List, 
        field_name: str, 
        task_id: Optional[str]
    ) -> tuple[List, bool]:
        """Ottimizza campi array"""
        
        if len(array_data) <= self.max_array_items:
            return array_data, False
        
        # Preserva i primi elementi più importanti
        if field_name == "next_steps":
            # Per next_steps, preserva i primi (più importanti)
            optimized = array_data[:self.max_array_items - 1]
            optimized.append(f"... and {len(array_data) - len(optimized)} more steps")
        else:
            # Per altri array, preserva inizio e fine
            half_limit = self.max_array_items // 2
            optimized = array_data[:half_limit]
            optimized.append(f"... [{len(array_data) - self.max_array_items} items omitted] ...")
            optimized.extend(array_data[-half_limit:])
        
        logger.info(f"Task {task_id}: Array '{field_name}' truncated from {len(array_data)} to {len(optimized)} items")
        return optimized, True
    
    def _emergency_truncate(
        self, 
        output: Dict[str, Any], 
        task_id: Optional[str]
    ) -> tuple[Dict[str, Any], bool]:
        """Truncation di emergenza se l'output è ancora troppo lungo"""
        
        # Mantieni solo i campi più critici
        critical_fields = [
            "task_id", "status", "summary", "detailed_results_json"
        ]
        
        emergency_output = {}
        
        for field in critical_fields:
            if field in output:
                if field == "summary":
                    # Ultra-truncate summary
                    summary = str(output[field])[:1000]
                    emergency_output[field] = summary + " [Emergency truncation applied]"
                elif field == "detailed_results_json":
                    # Ultra-truncate detailed results
                    detailed = str(output[field])[:10000]
                    if len(str(output[field])) > 10000:
                        detailed += " [Emergency truncation applied]"
                    emergency_output[field] = detailed
                else:
                    emergency_output[field] = output[field]
        
        # Aggiungi metadata di emergenza
        emergency_output["_emergency_truncation"] = {
            "applied": True,
            "timestamp": datetime.now().isoformat(),
            "original_fields": list(output.keys()),
            "preserved_fields": list(emergency_output.keys())
        }
        
        logger.warning(f"Task {task_id}: Emergency truncation applied to prevent system issues")
        return emergency_output, True
    
    def create_chunked_output_strategy(
        self, 
        large_data: Dict[str, Any], 
        task_id: str
    ) -> Dict[str, Any]:
        """
        Strategia per gestire output molto grandi dividendoli in chunks
        """
        
        # Per implementazioni future - output in multiple parti
        # Utile per liste di contatti molto grandi, etc.
        
        chunk_metadata = {
            "chunked_output": True,
            "task_id": task_id,
            "total_data_size": len(json.dumps(large_data, default=str)),
            "chunk_strategy": "future_implementation",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "summary": "Large output detected - chunking strategy recommended for future implementation",
            "metadata": chunk_metadata,
            "preview_data": str(large_data)[:2000] + "... [Preview only]"
        }
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche di ottimizzazione"""
        return {
            **self.processing_stats,
            "optimization_rate": (
                self.processing_stats["optimized_outputs"] / 
                max(self.processing_stats["total_processed"], 1)
            ),
            "truncation_rate": (
                self.processing_stats["truncated_outputs"] / 
                max(self.processing_stats["total_processed"], 1)
            )
        }

# Istanza globale
output_length_manager = OutputLengthManager()

def optimize_agent_output(
    task_output: Dict[str, Any], 
    task_id: Optional[str] = None
) -> tuple[Dict[str, Any], bool, List[str]]:
    """Helper function per ottimizzazione output"""
    return output_length_manager.optimize_task_output(task_output, task_id)

if __name__ == "__main__":
    # Test
    test_output = {
        "task_id": "test",
        "status": "completed",
        "summary": "This is a very long summary " * 200,  # Molto lungo
        "detailed_results_json": json.dumps({"contacts": [{"name": f"Contact {i}"} for i in range(200)]}),
        "next_steps": [f"Step {i}" for i in range(150)]
    }
    
    optimized, modified, mods = optimize_agent_output(test_output, "test_task")
    print(f"Modified: {modified}")
    print(f"Modifications: {mods}")
    print(f"Optimized length: {len(json.dumps(optimized))}")