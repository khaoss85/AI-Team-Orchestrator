#!/usr/bin/env python3
"""
Output Chunking Helper for Large Agent Responses
Handles splitting large contact lists and deliverables into manageable chunks
"""
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class OutputChunker:
    """Helper class to chunk large agent outputs"""
    
    MAX_JSON_SIZE = 45000  # Leave some buffer under 50KB limit
    MAX_CONTACTS_PER_CHUNK = 25  # Reasonable chunk size for contacts
    
    @classmethod
    def chunk_contact_list(cls, contacts_data: Any) -> List[Dict[str, Any]]:
        """
        Split a large contact list into smaller chunks
        
        Args:
            contacts_data: Can be dict with 'contacts' key or list of contacts
            
        Returns:
            List of chunked contact data dictionaries
        """
        try:
            # Extract contacts list
            if isinstance(contacts_data, dict) and 'contacts' in contacts_data:
                contacts = contacts_data['contacts']
                metadata = {k: v for k, v in contacts_data.items() if k != 'contacts'}
            elif isinstance(contacts_data, list):
                contacts = contacts_data
                metadata = {}
            else:
                logger.warning(f"Unexpected contacts_data format: {type(contacts_data)}")
                return [contacts_data]
            
            if len(contacts) <= cls.MAX_CONTACTS_PER_CHUNK:
                return [contacts_data]  # No chunking needed
            
            chunks = []
            total_chunks = (len(contacts) + cls.MAX_CONTACTS_PER_CHUNK - 1) // cls.MAX_CONTACTS_PER_CHUNK
            
            for i in range(0, len(contacts), cls.MAX_CONTACTS_PER_CHUNK):
                chunk_contacts = contacts[i:i + cls.MAX_CONTACTS_PER_CHUNK]
                chunk_num = (i // cls.MAX_CONTACTS_PER_CHUNK) + 1
                
                chunk_data = {
                    **metadata,
                    'contacts': chunk_contacts,
                    'chunk_info': {
                        'chunk_number': chunk_num,
                        'total_chunks': total_chunks,
                        'contacts_in_chunk': len(chunk_contacts),
                        'total_contacts': len(contacts)
                    }
                }
                chunks.append(chunk_data)
            
            logger.info(f"Split {len(contacts)} contacts into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking contacts: {e}")
            return [contacts_data]
    
    @classmethod
    def truncate_if_needed(cls, json_str: str, data_type: str = "data") -> str:
        """
        Truncate JSON string if it exceeds size limits
        
        Args:
            json_str: The JSON string to check
            data_type: Type of data for logging
            
        Returns:
            Truncated JSON string if needed
        """
        if len(json_str) <= cls.MAX_JSON_SIZE:
            return json_str
        
        logger.warning(f"Output size {len(json_str)} exceeds limit {cls.MAX_JSON_SIZE} for {data_type}")
        
        try:
            # Try to parse and intelligently truncate
            data = json.loads(json_str)
            
            # If it's contact data, chunk it
            if isinstance(data, dict) and ('contacts' in data or 'contact_list' in data):
                chunks = cls.chunk_contact_list(data)
                if chunks:
                    # Return first chunk with chunk info
                    first_chunk = chunks[0]
                    first_chunk['_truncation_info'] = {
                        'truncated': True,
                        'total_chunks_available': len(chunks),
                        'reason': 'Output size exceeded limit'
                    }
                    return json.dumps(first_chunk)
            
            # For other data types, try to truncate gracefully
            if isinstance(data, dict):
                # Keep essential fields, truncate others
                essential_fields = ['summary', 'actionable_insights', 'visual_summary', 'structured_content']
                truncated_data = {}
                
                for field in essential_fields:
                    if field in data:
                        truncated_data[field] = data[field]
                
                # Add truncation info
                truncated_data['_truncation_info'] = {
                    'truncated': True,
                    'original_size': len(json_str),
                    'original_fields': list(data.keys()),
                    'reason': 'Output size exceeded limit'
                }
                
                return json.dumps(truncated_data)
            
        except json.JSONDecodeError:
            logger.error(f"Could not parse JSON for intelligent truncation")
        
        # Fallback: simple string truncation
        truncated = json_str[:cls.MAX_JSON_SIZE - 200]
        truncated += '... [TRUNCATED: Output exceeded size limit]'
        
        return truncated
    
    @classmethod
    def create_summary_for_large_dataset(cls, data: Any, data_type: str = "contacts") -> Dict[str, Any]:
        """
        Create a summary for large datasets that would exceed limits
        
        Args:
            data: The large dataset
            data_type: Type of data
            
        Returns:
            Summary dictionary
        """
        summary = {
            'data_type': data_type,
            'summary': f'Large {data_type} dataset created successfully',
            'statistics': {},
            'sample_entries': [],
            'truncation_reason': 'Dataset too large for single response'
        }
        
        try:
            if isinstance(data, dict) and 'contacts' in data:
                contacts = data['contacts']
                summary['statistics'] = {
                    'total_contacts': len(contacts),
                    'unique_companies': len(set(c.get('company', '') for c in contacts if c.get('company'))),
                    'countries_covered': len(set(c.get('country', '') for c in contacts if c.get('country'))),
                    'roles_distribution': {}
                }
                
                # Role distribution
                roles = [c.get('role', '') for c in contacts if c.get('role')]
                for role in set(roles):
                    summary['statistics']['roles_distribution'][role] = roles.count(role)
                
                # Sample entries (first 3)
                summary['sample_entries'] = contacts[:3]
                
            elif isinstance(data, list):
                summary['statistics']['total_items'] = len(data)
                summary['sample_entries'] = data[:3]
                
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            summary['error'] = str(e)
        
        return summary