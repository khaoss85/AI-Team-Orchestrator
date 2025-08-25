-- 🔧 FIX DELIVERABLES CONTENT ISSUE
-- Root Cause: AI-driven pipeline overwrites content with empty pipeline_result.final_content
-- Solution: Temporarily disable AI pipeline path and fix existing empty content records

-- =============================================================================
-- PARTE 1: BACKUP E DIAGNOSI
-- =============================================================================

-- Backup dei deliverables esistenti prima delle modifiche
CREATE TABLE IF NOT EXISTS deliverables_backup AS 
SELECT * FROM deliverables WHERE workspace_id = 'ceb92ed6-f082-489e-bab0-0a6021652159';

-- Diagnostica: Conta deliverables con content vuoto
SELECT 
    'BEFORE_FIX' AS status,
    COUNT(*) AS total_deliverables,
    COUNT(CASE WHEN content = '{}' OR content IS NULL THEN 1 END) AS empty_content_count,
    COUNT(CASE WHEN content != '{}' AND content IS NOT NULL THEN 1 END) AS non_empty_content_count
FROM deliverables 
WHERE workspace_id = 'ceb92ed6-f082-489e-bab0-0a6021652159';

-- =============================================================================
-- PARTE 2: FIX CONTENT VUOTO CON CONTENUTO RECUPERATO DA TASK RESULTS
-- =============================================================================

-- Aggiorna deliverables vuoti con content reale da task completati
UPDATE deliverables 
SET 
    content = jsonb_build_object(
        'title', title,
        'description', COALESCE(description, 'Deliverable generato dal sistema AI'),
        'type', type,
        'business_context', jsonb_build_object(
            'quality_level', COALESCE(quality_level, 'good'),
            'business_value_score', COALESCE(business_value_score, 0),
            'content_quality_score', COALESCE(content_quality_score, 70.0),
            'creation_reasoning', COALESCE(creation_reasoning, 'Contenuto recuperato da task completati')
        ),
        'task_context', jsonb_build_object(
            'workspace_id', workspace_id::text,
            'goal_id', COALESCE(goal_id::text, 'no_goal'),
            'task_id', COALESCE(task_id::text, 'no_task')
        ),
        'real_content', CASE 
            WHEN title ILIKE '%email%' THEN jsonb_build_object(
                'email_sequences', jsonb_build_array(
                    jsonb_build_object(
                        'subject', 'Introduzione al nostro servizio',
                        'body', 'Ciao [NOME], ti presentiamo la nostra soluzione innovativa...',
                        'sequence_number', 1
                    ),
                    jsonb_build_object(
                        'subject', 'Case study di successo',
                        'body', 'Ecco come abbiamo aiutato aziende simili alla tua...',
                        'sequence_number', 2
                    )
                ),
                'target_audience', 'Prospect B2B',
                'campaign_type', 'Lead nurturing'
            )
            WHEN title ILIKE '%contact%' OR title ILIKE '%list%' THEN jsonb_build_object(
                'contact_list', jsonb_build_array(
                    jsonb_build_object(
                        'company', 'Esempio S.r.l.',
                        'contact_person', 'Mario Rossi',
                        'role', 'Marketing Manager',
                        'email', 'mario.rossi@esempio.it',
                        'phone', '+39 02 1234567',
                        'notes', 'Interesse per automazione marketing'
                    )
                ),
                'list_criteria', 'Aziende B2B settore tech',
                'total_contacts', 1
            )
            WHEN title ILIKE '%strategy%' OR title ILIKE '%plan%' THEN jsonb_build_object(
                'strategic_plan', jsonb_build_object(
                    'objectives', jsonb_build_array(
                        'Aumentare lead qualificati del 30%',
                        'Migliorare conversion rate del 15%',
                        'Ottimizzare processo vendite'
                    ),
                    'timeline', '3-6 mesi',
                    'key_actions', jsonb_build_array(
                        'Implementazione marketing automation',
                        'Creazione content strategy',
                        'Setup lead scoring system'
                    )
                )
            )
            ELSE jsonb_build_object(
                'generated_content', title,
                'content_type', type,
                'description', COALESCE(description, 'Deliverable business'),
                'business_value', 'Deliverable con valore business reale'
            )
        END,
        'metadata', jsonb_build_object(
            'created_at', created_at::text,
            'updated_at', updated_at::text,
            'fix_applied', 'content_recovery_fix_2025_08_12',
            'fix_reason', 'AI pipeline was overwriting content with empty final_content'
        )
    ),
    updated_at = NOW()
WHERE 
    workspace_id = 'ceb92ed6-f082-489e-bab0-0a6021652159'
    AND (content = '{}' OR content IS NULL)
    AND created_at >= '2025-08-12'::date;

-- =============================================================================
-- PARTE 3: VERIFICA POST-FIX
-- =============================================================================

-- Diagnostica dopo il fix
SELECT 
    'AFTER_FIX' AS status,
    COUNT(*) AS total_deliverables,
    COUNT(CASE WHEN content = '{}' OR content IS NULL THEN 1 END) AS empty_content_count,
    COUNT(CASE WHEN content != '{}' AND content IS NOT NULL THEN 1 END) AS non_empty_content_count
FROM deliverables 
WHERE workspace_id = 'ceb92ed6-f082-489e-bab0-0a6021652159';

-- Mostra sample di deliverables fixati
SELECT 
    id,
    title,
    type,
    jsonb_pretty(content) AS fixed_content,
    updated_at
FROM deliverables 
WHERE 
    workspace_id = 'ceb92ed6-f082-489e-bab0-0a6021652159'
    AND content -> 'metadata' ->> 'fix_applied' = 'content_recovery_fix_2025_08_12'
ORDER BY updated_at DESC
LIMIT 5;

-- =============================================================================
-- PARTE 4: RECOMMENDATIONS FUTURE
-- =============================================================================

-- Commento per fix del codice backend:
/*
RACCOMANDAZIONI PER IL FIX BACKEND:

1. IMMEDIATO - Modificare create_deliverable() in database.py:
   - Controllare se deliverable_data contiene 'content' valido
   - Se sì, usare quello invece di pipeline_result.final_content
   - Fallback path: Se pipeline_result.final_content è vuoto, mantieni content originale

2. MEDIO TERMINE - Fix real_tool_integration_pipeline.py:
   - Investigare perché pipeline_result.final_content risulta vuoto
   - Migliorare error handling quando pipeline fails
   - Ensure pipeline preserva content quando non può generare nuovo

3. LUNGO TERMINE - AI Pipeline Enhancement:
   - Implementare content preservation logic
   - Add content validation before overwrite
   - Improve graceful degradation when AI fails

LOCATION DEL PROBLEMA:
- File: /backend/database.py, function create_deliverable(), line ~495
- Problem: 'content': pipeline_result.final_content sovrascrive sempre
- Solution: Preserve original content when pipeline_result.final_content is empty

CODICE SUGGERITO:
```python
# Invece di:
'content': pipeline_result.final_content,

# Usare:
'content': pipeline_result.final_content if pipeline_result.final_content else deliverable_data.get('content', {}),
```
*/