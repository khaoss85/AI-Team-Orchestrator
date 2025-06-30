# backend/utils/semantic_json_helpers.py
"""
🧠 SEMANTIC JSON HELPER FUNCTIONS
Intelligent content analysis and extraction for robust JSON parsing
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SemanticJSONHelpers:
    """Helper functions for semantic analysis and intelligent content extraction"""
    
    @staticmethod
    def find_intelligent_json_start(text: str) -> int:
        """🧠 Find probable JSON start using semantic analysis"""
        
        # Semantic patterns for task-related JSON starts
        intelligent_patterns = [
            r'\{\s*"task_id"\s*:\s*"[^"]*"',
            r'\{\s*"status"\s*:\s*"[^"]*"',
            r'\{\s*"summary"\s*:\s*"[^"]*"',
            r'\{\s*"id"\s*:\s*"[^"]*"',
            # Look for JSON after common introduction phrases
            r'(?:result|output|response|here|following):\s*\{',
        ]
        
        best_match = -1
        best_score = 0
        
        for pattern in intelligent_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Score based on how likely this is the correct start
                score = 1
                start_pos = match.start()
                
                # Prefer matches that start with task-specific fields
                if '"task_id"' in match.group() or '"status"' in match.group():
                    score += 2
                
                # Prefer matches earlier in the text
                score += max(0, (1000 - start_pos) / 1000)
                
                if score > best_score:
                    best_score = score
                    best_match = start_pos
        
        # Fallback to simple { search
        if best_match == -1:
            best_match = text.find('{')
        
        return best_match
    
    @staticmethod
    def repair_with_semantic_analysis(json_fragment: str, expected_schema: Optional[Dict] = None) -> Optional[str]:
        """🧠 Repair JSON using semantic understanding of task structure"""
        
        if not json_fragment.strip():
            return None
        
        # Ensure starts with {
        if not json_fragment.strip().startswith('{'):
            return None
        
        lines = json_fragment.split('\n')
        valid_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Keep lines that look like valid JSON fields
            if re.match(r'^\s*"[^"]+"\s*:\s*["\{]', line):
                valid_content.append(line)
            elif line == '{' or line == '}':
                valid_content.append(line)
            elif line.endswith(',') and '"' in line and ':' in line:
                valid_content.append(line)
            else:
                # Stop at first obviously broken line
                break
        
        if len(valid_content) < 2:
            return None
        
        # Reconstruct with proper JSON structure
        reconstructed = '{\n  ' + '\n  '.join(valid_content[1:-1]) + '\n}'
        
        # Clean up structure
        reconstructed = re.sub(r',(\s*\})', r'\1', reconstructed)
        
        return reconstructed
    
    @staticmethod
    def repair_with_pattern_completion(json_fragment: str, expected_schema: Optional[Dict] = None) -> Optional[str]:
        """🔧 Repair using common task output patterns"""
        
        # Common task output patterns to complete
        common_patterns = {
            '"task_id"': '"task_id": "unknown"',
            '"status"': '"status": "completed"',
            '"summary"': '"summary": "Task completed successfully"'
        }
        
        # If fragment has incomplete fields, try to complete them
        for pattern, completion in common_patterns.items():
            if pattern in json_fragment and f'{pattern}:' not in json_fragment:
                # Field name without value - complete it
                json_fragment = json_fragment.replace(pattern, completion)
        
        # Try to balance braces
        open_braces = json_fragment.count('{')
        close_braces = json_fragment.count('}')
        
        if open_braces > close_braces:
            json_fragment += '}' * (open_braces - close_braces)
        
        return json_fragment
    
    @staticmethod
    def repair_with_structure_analysis(json_fragment: str, expected_schema: Optional[Dict] = None) -> Optional[str]:
        """🔍 Repair using structural analysis"""
        
        # Find the last complete field
        field_pattern = r'"([^"]+)"\s*:\s*"([^"]*)"'
        matches = list(re.finditer(field_pattern, json_fragment))
        
        if not matches:
            return None
        
        # Find end of last complete field
        last_match = matches[-1]
        end_pos = last_match.end()
        
        # Take content up to last complete field
        clean_content = json_fragment[:end_pos]
        
        # Ensure proper closure
        if not clean_content.endswith('}'):
            if not clean_content.endswith(','):
                clean_content += ','
            clean_content += '\n  "completed": true\n}'
        
        return clean_content
    
    @staticmethod
    def extract_task_id_semantic(raw_output: str) -> Optional[str]:
        """🧠 Extract task ID using semantic analysis"""
        
        patterns = [
            r'"task_id"\s*:\s*"([^"]+)"',
            r'"id"\s*:\s*"([^"]+)"',
            r'task[_\s]+id[:\s]+([a-f0-9\-]+)',
            r'ID[:\s]+([a-f0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def extract_status_semantic(raw_output: str) -> str:
        """🧠 Extract status using semantic analysis"""
        
        # Direct status patterns
        status_patterns = [
            r'"status"\s*:\s*"([^"]+)"',
            r'status[:\s]+([a-zA-Z]+)',
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, raw_output, re.IGNORECASE)
            if match:
                status = match.group(1).lower()
                if status in ["completed", "failed", "requires_handoff"]:
                    return status
        
        # Semantic analysis for status
        error_indicators = ["error", "failed", "exception", "unable", "cannot"]
        success_indicators = ["completed", "success", "finished", "done", "achieved"]
        handoff_indicators = ["handoff", "manual", "requires", "intervention"]
        
        content_lower = raw_output.lower()
        
        if any(indicator in content_lower for indicator in error_indicators):
            return "failed"
        elif any(indicator in content_lower for indicator in handoff_indicators):
            return "requires_handoff"
        else:
            return "completed"
    
    @staticmethod
    def extract_summary_semantic(raw_output: str) -> Optional[str]:
        """🧠 Extract summary using semantic analysis"""
        
        # Direct summary patterns
        summary_patterns = [
            r'"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
            r'summary[:\s]+([^\n]+)',
            r'Summary:\s*([^\n]+)',
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, raw_output, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Fallback: extract first meaningful sentence
        sentences = re.split(r'[.!?]+', raw_output)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and not sentence.startswith('{'):
                return sentence[:200] + ("..." if len(sentence) > 200 else "")
        
        return None
    
    @staticmethod
    def extract_detailed_results_semantic(raw_output: str) -> Optional[str]:
        """🧠 Extract detailed results using semantic analysis"""
        
        # Look for existing detailed_results_json
        patterns = [
            r'"detailed_results_json"\s*:\s*"([^"]*(?:\\.[^"]*)*)"',
            r'"detailed_results_json"\s*:\s*(\{[^}]*\})',
            r'"details"\s*:\s*(\{[^}]*\})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_output, re.DOTALL)
            if match:
                return match.group(1)
        
        # Generate from available content
        content_data = {
            "content_type": "semantic_extraction",
            "raw_content_length": len(raw_output),
            "extraction_timestamp": datetime.now().isoformat(),
            "content_preview": raw_output[:500] if raw_output else ""
        }
        
        return json.dumps(content_data)
    
    @staticmethod
    def analyze_content_for_status(raw_output: str) -> str:
        """🧠 Analyze content to determine likely status"""
        return SemanticJSONHelpers.extract_status_semantic(raw_output)
    
    @staticmethod
    def analyze_content_for_summary(raw_output: str) -> str:
        """🧠 Analyze content to generate summary"""
        extracted = SemanticJSONHelpers.extract_summary_semantic(raw_output)
        return extracted or "Content processed successfully"
    
    @staticmethod
    def analyze_content_indicators(raw_output: str) -> Dict[str, Any]:
        """🧠 Analyze content for various indicators"""
        
        indicators = {
            "has_json_structure": '{' in raw_output and '}' in raw_output,
            "has_error_keywords": any(word in raw_output.lower() for word in ["error", "failed", "exception"]),
            "has_success_keywords": any(word in raw_output.lower() for word in ["success", "completed", "done"]),
            "content_length": len(raw_output),
            "line_count": len(raw_output.split('\n')),
            "appears_truncated": raw_output.endswith(('...', '"', ',')),
            "has_task_keywords": any(word in raw_output.lower() for word in ["task", "status", "summary"])
        }
        
        return indicators
    
    @staticmethod
    def extract_any_meaningful_content(raw_output: str) -> Optional[str]:
        """🧠 Extract ANY meaningful content as last resort"""
        
        if not raw_output or len(raw_output.strip()) < 5:
            return None
        
        # Try to find any coherent sentence or phrase
        meaningful_patterns = [
            r'[A-Z][^.!?]*[.!?]',  # Complete sentences
            r'[A-Z][^.!?\n]{20,}',  # Long phrases starting with capital
            r'[a-zA-Z][^{}\n]{30,}',  # Any substantial text
        ]
        
        for pattern in meaningful_patterns:
            matches = re.findall(pattern, raw_output)
            if matches:
                # Return the longest match
                longest = max(matches, key=len)
                return longest.strip()[:200] + ("..." if len(longest) > 200 else "")
        
        # Last resort: return first substantial chunk
        lines = [line.strip() for line in raw_output.split('\n') if line.strip()]
        substantial_lines = [line for line in lines if len(line) > 10 and not line.startswith('{')]
        
        if substantial_lines:
            return substantial_lines[0][:150] + ("..." if len(substantial_lines[0]) > 150 else "")
        
        return f"Content processed (length: {len(raw_output)} characters)"

# Export helper functions for direct use
find_intelligent_json_start = SemanticJSONHelpers.find_intelligent_json_start
repair_with_semantic_analysis = SemanticJSONHelpers.repair_with_semantic_analysis
repair_with_pattern_completion = SemanticJSONHelpers.repair_with_pattern_completion
repair_with_structure_analysis = SemanticJSONHelpers.repair_with_structure_analysis
extract_task_id_semantic = SemanticJSONHelpers.extract_task_id_semantic
extract_status_semantic = SemanticJSONHelpers.extract_status_semantic
extract_summary_semantic = SemanticJSONHelpers.extract_summary_semantic
extract_detailed_results_semantic = SemanticJSONHelpers.extract_detailed_results_semantic
analyze_content_for_status = SemanticJSONHelpers.analyze_content_for_status
analyze_content_for_summary = SemanticJSONHelpers.analyze_content_for_summary
analyze_content_indicators = SemanticJSONHelpers.analyze_content_indicators
extract_any_meaningful_content = SemanticJSONHelpers.extract_any_meaningful_content