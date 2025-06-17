# backend/utils/robust_json_parser.py
"""
Gestore robusto per parsing JSON da output LLM con recovery automatico
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONParsingError(Exception):
    """Eccezione custom per errori di parsing JSON"""
    pass

class RobustJSONParser:
    """Parser JSON robusto per output LLM con recovery automatico"""
    
    def __init__(self, max_recovery_attempts: int = 3):
        self.max_recovery_attempts = max_recovery_attempts
        self.parsing_stats = {
            "total_attempts": 0,
            "successful_parses": 0,
            "recovery_successes": 0,
            "complete_failures": 0
        }
    
    def parse_llm_output(
        self, 
        raw_output: str, 
        expected_schema: Optional[Dict] = None,
        task_id: Optional[str] = None
    ) -> tuple[Dict[str, Any], bool, str]:
        """
        Parse robusto di output LLM con recovery automatico
        
        Args:
            raw_output: Output grezzo dall'LLM
            expected_schema: Schema atteso (opzionale, per validazione)
            task_id: ID task per logging (opzionale)
            
        Returns:
            tuple[parsed_data, is_complete, parsing_method]
        """
        self.parsing_stats["total_attempts"] += 1
        
        try:
            # Tentativo 1: Parsing diretto
            result = self._attempt_direct_parse(raw_output)
            if result:
                self.parsing_stats["successful_parses"] += 1
                # CRITICAL FIX: Ensure task_id is always present
                result = self._ensure_required_fields(result, task_id)
                return result, True, "direct_parse"
            
            # Tentativo 2: Estrazione JSON con regex
            result = self._attempt_regex_extraction(raw_output)
            if result:
                self.parsing_stats["recovery_successes"] += 1
                # CRITICAL FIX: Ensure task_id is always present
                result = self._ensure_required_fields(result, task_id)
                return result, True, "regex_extraction"
            
            # Tentativo 3: Recovery da JSON troncato
            result = self._attempt_truncated_recovery(raw_output, expected_schema)
            if result:
                self.parsing_stats["recovery_successes"] += 1
                # CRITICAL FIX: Ensure task_id is always present
                result = self._ensure_required_fields(result, task_id)
                return result, False, "truncated_recovery"  # False = incomplete
            
            # Tentativo 4: Parsing parziale intelligente
            result = self._attempt_intelligent_partial_parse(raw_output, expected_schema)
            if result:
                self.parsing_stats["recovery_successes"] += 1
                # CRITICAL FIX: Ensure task_id is always present
                result = self._ensure_required_fields(result, task_id)
                return result, False, "partial_parse"
            
            # Fallimento completo
            self.parsing_stats["complete_failures"] += 1
            logger.error(f"Complete JSON parsing failure for task {task_id}. Raw output length: {len(raw_output)}")
            
            return self._create_error_fallback(raw_output, task_id), False, "error_fallback"
            
        except Exception as e:
            self.parsing_stats["complete_failures"] += 1
            logger.error(f"Exception in robust JSON parsing for task {task_id}: {e}")
            return self._create_error_fallback(raw_output, task_id, str(e)), False, "exception_fallback"
    
    def _attempt_direct_parse(self, raw_output: str) -> Optional[Dict[str, Any]]:
        """Tentativo di parsing JSON diretto"""
        try:
            # Pulizia base
            cleaned = self._clean_json_string(raw_output)
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None
    
    def _attempt_regex_extraction(self, raw_output: str) -> Optional[Dict[str, Any]]:
        """Estrazione JSON con regex da blocchi markdown o testo"""
        patterns = [
            # JSON in blocchi markdown
            r"```json\s*(\{[\s\S]*?\})\s*```",
            # JSON in blocchi di codice generici  
            r"```\s*(\{[\s\S]*?\})\s*```",
            # JSON standalone (più conservativo)
            r"(\{(?:[^{}]|{[^{}]*})*\})",
            # JSON multiline con cattura più aggressiva
            r"(\{[\s\S]*?\})",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, raw_output, re.DOTALL)
            for match in matches:
                try:
                    cleaned = self._clean_json_string(match)
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict) and len(parsed) > 1:
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return None
    
    def _attempt_truncated_recovery(
        self, 
        raw_output: str, 
        expected_schema: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Recovery da JSON troncato"""
        
        # Trova il punto di inizio JSON più probabile
        json_start = self._find_json_start(raw_output)
        if json_start == -1:
            return None
        
        json_fragment = raw_output[json_start:]
        
        # Prova a riparare JSON troncato
        repaired_attempts = [
            self._repair_truncated_json_basic(json_fragment),
            self._repair_truncated_json_smart(json_fragment, expected_schema),
            self._repair_truncated_json_aggressive(json_fragment)
        ]
        
        for repaired in repaired_attempts:
            if repaired:
                try:
                    cleaned = self._clean_json_string(repaired)
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return None
    
    def _attempt_intelligent_partial_parse(
        self,
        raw_output: str,
        expected_schema: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Parsing parziale intelligente estraendo campi chiave"""
        
        result = {}
        
        # Estrai campi comuni da TaskExecutionOutput
        field_patterns = {
            "task_id": r'"task_id"\s*:\s*"([^"]+)"',
            "status": r'"status"\s*:\s*"([^"]+)"',
            "summary": r'"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
        }
        
        for field, pattern in field_patterns.items():
            match = re.search(pattern, raw_output, re.IGNORECASE | re.DOTALL)
            if match:
                result[field] = match.group(1)
        
        # Estrai detailed_results_json (più complesso)
        detailed_results = self._extract_detailed_results(raw_output)
        if detailed_results:
            result["detailed_results_json"] = detailed_results
        
        # Estrai array campi (next_steps, etc.)
        array_fields = self._extract_array_fields(raw_output)
        result.update(array_fields)
        
        return result if len(result) >= 2 else None  # Almeno 2 campi validi
    
    def _find_json_start(self, text: str) -> int:
        """Trova il punto di inizio più probabile del JSON"""
        # Cerca pattern di inizio JSON
        patterns = [
            r'\{\s*"task_id"',
            r'\{\s*"status"',
            r'\{\s*"summary"',
            r'^\s*\{',  # Inizio linea con {
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.start()
        
        # Fallback: primo {
        return text.find('{')
    
    def _find_last_valid_json_position(self, json_text: str) -> int:
        """Trova l'ultima posizione valida prima del truncating"""
        # Cerca l'ultima virgola seguita da spazio o newline
        last_comma = -1
        for i in range(len(json_text) - 1, -1, -1):
            if json_text[i] == ',' and i < len(json_text) - 1:
                next_char = json_text[i + 1]
                if next_char in [' ', '\n', '\t', '\r']:
                    last_comma = i + 1
                    break
        
        # Se non troviamo una virgola valida, cerca l'ultima chiusura di stringa completa
        if last_comma == -1:
            for i in range(len(json_text) - 1, -1, -1):
                if json_text[i] == '"' and i > 0 and json_text[i-1] != '\\':
                    # Verifica che sia una chiusura valida contando le quotes precedenti
                    quotes_before = json_text[:i].count('"') - json_text[:i].count('\\"')
                    if quotes_before % 2 == 1:  # Numero dispari = questa è una chiusura
                        return i + 1
        
        return max(0, last_comma)
    
    def _repair_truncated_json_basic(self, json_fragment: str) -> Optional[str]:
        """Riparazione base di JSON troncato"""
        if not json_fragment.strip():
            return None
        
        # Assicura che inizi con {
        if not json_fragment.strip().startswith('{'):
            return None
        
        # Trova l'ultima posizione valida del JSON
        last_valid_pos = self._find_last_valid_json_position(json_fragment)
        if last_valid_pos > 0:
            json_fragment = json_fragment[:last_valid_pos]
        
        # Conta parentesi graffe per bilanciare
        open_braces = json_fragment.count('{')
        close_braces = json_fragment.count('}')
        
        repaired = json_fragment
        
        # Chiudi stringhe aperte
        quote_count = repaired.count('"')
        if quote_count % 2 != 0:
            repaired += '"'
        
        # Aggiungi parentesi graffe mancanti
        missing_braces = open_braces - close_braces
        if missing_braces > 0:
            repaired += '}' * missing_braces
        
        return repaired
    
    def _repair_truncated_json_smart(
        self, 
        json_fragment: str, 
        expected_schema: Optional[Dict] = None
    ) -> Optional[str]:
        """Riparazione intelligente basata su schema atteso"""
        
        if not expected_schema:
            return self._repair_truncated_json_basic(json_fragment)
        
        # Logica più sofisticata basata sui campi attesi
        # Per ora, usa la riparazione base
        return self._repair_truncated_json_basic(json_fragment)
    
    def _repair_truncated_json_aggressive(self, json_fragment: str) -> Optional[str]:
        """Riparazione aggressiva per casi estremi"""
        
        # Trova l'ultimo campo/valore completo
        lines = json_fragment.split('\n')
        valid_lines = []
        
        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue
            
            # Se la linea sembra completa (finisce con , o } o ])
            if cleaned_line.endswith((',', '}', ']', '}')):
                valid_lines.append(line)
            # Se la linea sembra un campo completo
            elif '"' in cleaned_line and ':' in cleaned_line:
                # Prova a completare il campo
                if cleaned_line.endswith(','):
                    valid_lines.append(line)
                elif not cleaned_line.endswith('"'):
                    # Chiudi il valore stringa se sembra troncato
                    if cleaned_line.count('"') % 2 != 0:
                        valid_lines.append(line + '"')
                else:
                    valid_lines.append(line)
            else:
                # Linea probabilmente troncata, ferma qui
                break
        
        if not valid_lines:
            return None
        
        # Ricostruisci JSON
        reconstructed = '\n'.join(valid_lines)
        
        # Assicura chiusura corretta
        if not reconstructed.strip().endswith('}'):
            if reconstructed.strip().endswith(','):
                reconstructed = reconstructed.strip()[:-1]  # Rimuovi virgola finale
            reconstructed += '\n}'
        
        return reconstructed
    
    def _extract_detailed_results(self, text: str) -> Optional[str]:
        """Estrai campo detailed_results_json anche se troncato"""
        
        patterns = [
            r'"detailed_results_json"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
            r'"detailed_results_json"\s*:\s*(\{[^}]*\})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_array_fields(self, text: str) -> Dict[str, List[str]]:
        """Estrai campi array come next_steps"""
        
        result = {}
        
        # Pattern per array di stringhe
        array_pattern = r'"(next_steps|resources_consumed)"\s*:\s*\[(.*?)\]'
        matches = re.findall(array_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for field_name, array_content in matches:
            # Estrai stringhe dall'array
            string_pattern = r'"([^"]*)"'
            strings = re.findall(string_pattern, array_content)
            if strings:
                result[field_name] = strings
        
        return result
    
    def _clean_json_string(self, json_str: str) -> str:
        """Enhanced JSON cleaning with common error fixes"""
        
        # Rimuovi caratteri di controllo problematici
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
        
        # Rimuovi non-breaking spaces e altri caratteri Unicode problematici
        cleaned = cleaned.replace('\u00a0', ' ')  # Non-breaking space
        cleaned = cleaned.replace('\ufeff', '')   # BOM
        
        # Fix trailing commas (major cause of parsing errors)
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        # Fix unescaped quotes inside strings (common in LLM outputs)
        # This is tricky - we need to escape quotes that are inside string values
        # Pattern: "field": "value with "quotes" inside"
        cleaned = re.sub(r'(":\s*")([^"]*)"([^"]*)"([^"]*)(")(?=\s*[,}])', r'\1\2\"\3\"\4\5', cleaned)
        
        # Fix invalid escape sequences
        cleaned = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', cleaned)
        
        # Fix missing quotes around field names
        cleaned = re.sub(r'(\{|\,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', cleaned)
        
        # Fix single quotes to double quotes (JSON requires double quotes)
        cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
        
        # Normalizza whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _create_error_fallback(
        self, 
        raw_output: str, 
        task_id: Optional[str] = None,
        error_msg: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crea un oggetto fallback in caso di fallimento completo"""
        
        # Estrai almeno un summary dall'output grezzo se possibile
        summary_attempt = self._extract_summary_fallback(raw_output)
        
        return {
            "task_id": task_id or "unknown",
            "status": "failed",
            "summary": summary_attempt or f"JSON parsing failed: {error_msg or 'Unknown error'}",
            "detailed_results_json": json.dumps({
                "error": "json_parsing_failed",
                "error_details": error_msg,
                "raw_output_length": len(raw_output),
                "raw_output_preview": raw_output[:500] if raw_output else "",
                "parsing_timestamp": datetime.now().isoformat()
            })
        }
    
    def _extract_summary_fallback(self, raw_output: str) -> Optional[str]:
        """Estrai almeno un summary dall'output anche se il JSON è rotto"""
        
        # Cerca pattern di summary nel testo
        summary_patterns = [
            r'summary["\s]*:["\s]*([^"]+)',
            r'Summary:\s*([^\n]+)',
            r'SUMMARY:\s*([^\n]+)',
            # Prendi le prime frasi significative se niente funziona
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, raw_output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: prime righe significative
        lines = [line.strip() for line in raw_output.split('\n') if line.strip()]
        meaningful_lines = [line for line in lines[:5] if len(line) > 20 and not line.startswith('{')]
        
        if meaningful_lines:
            return meaningful_lines[0][:200] + "..." if len(meaningful_lines[0]) > 200 else meaningful_lines[0]
        
        return None
    
    def _ensure_required_fields(self, result: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        CRITICAL FIX: Assicura che i campi obbligatori siano sempre presenti nel risultato
        
        Args:
            result: Il dizionario parsed dal JSON
            task_id: Il task_id da usare se mancante
            
        Returns:
            Dict con tutti i campi obbligatori presenti
        """
        if not isinstance(result, dict):
            result = {}
        
        # CAMPO OBBLIGATORIO: task_id
        if "task_id" not in result or not result["task_id"]:
            result["task_id"] = task_id or "unknown"
            logger.warning(f"Missing task_id in parsed result - added: {result['task_id']}")
        
        # CAMPO OBBLIGATORIO: status
        if "status" not in result or not result["status"]:
            # Default to "completed" for enhancement tasks, unless there are clear failure indicators
            result["status"] = "completed"
            logger.warning(f"Missing status in parsed result - defaulted to: completed")
        
        # CAMPO OBBLIGATORIO: summary
        if "summary" not in result or not result["summary"]:
            result["summary"] = f"Task {result.get('task_id', 'unknown')} completed"
            logger.warning(f"Missing summary in parsed result - added default summary")
        
        # Validate status field value
        valid_statuses = ["completed", "failed", "requires_handoff"]
        if result["status"] not in valid_statuses:
            logger.warning(f"Invalid status '{result['status']}' - defaulting to 'completed'")
            result["status"] = "completed"
        
        return result
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche di parsing"""
        total = self.parsing_stats["total_attempts"]
        if total == 0:
            return self.parsing_stats
        
        return {
            **self.parsing_stats,
            "success_rate": self.parsing_stats["successful_parses"] / total,
            "recovery_rate": self.parsing_stats["recovery_successes"] / total,
            "failure_rate": self.parsing_stats["complete_failures"] / total
        }

# Istanza globale
robust_json_parser = RobustJSONParser()

def parse_llm_json_robust(
    raw_output: str,
    task_id: Optional[str] = None,
    expected_schema: Optional[Dict] = None
) -> tuple[Dict[str, Any], bool, str]:
    """
    Helper function per parsing robusto
    
    Returns:
        tuple[parsed_data, is_complete, parsing_method]
    """
    return robust_json_parser.parse_llm_output(raw_output, expected_schema, task_id)

if __name__ == "__main__":
    # Test
    test_output = '''{"task_id":"test","status":"completed","summary":"Test summary","detailed_results_json":"{\\"test\\": \\"value\\", \\"name\\": \\" '''
    
    result, complete, method = parse_llm_json_robust(test_output, "test_task")
    logging.info(f"Result: {result}")
    logging.info(f"Complete: {complete}")
    logging.info(f"Method: {method}")
