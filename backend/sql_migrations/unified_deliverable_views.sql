-- =====================================================================
-- UNIFIED DELIVERABLE SYSTEM - DATABASE-FIRST APPROACH
-- =====================================================================
-- Data: 2025-07-07
-- Scopo: Creare viste e stored procedures unificate per logica deliverable
-- Strategia: Database come Single Source of Truth per eliminare duplicazioni
-- =====================================================================

-- =====================================================================
-- 1. VISTA UNIFICATA ASSET & DELIVERABLE DATA
-- =====================================================================
CREATE OR REPLACE VIEW unified_asset_deliverable_view AS
SELECT 
    -- Asset data
    aa.id as asset_id,
    aa.workspace_id,
    aa.name as asset_name,
    aa.type as asset_type,
    aa.content as asset_content,
    aa.metadata as asset_metadata,
    aa.quality_score as asset_quality_score,
    aa.created_at as asset_created_at,
    aa.updated_at as asset_updated_at,
    
    -- Deliverable data  
    d.id as deliverable_id,
    d.name as deliverable_name,
    d.description as deliverable_description,
    d.deliverable_type as deliverable_type,
    d.status as deliverable_status,
    d.completed_assets as deliverable_content,
    d.metadata as deliverable_metadata,
    d.completion_percentage as deliverable_completion,
    d.created_at as deliverable_created_at,
    d.updated_at as deliverable_updated_at,
    
    -- Workspace context
    w.name as workspace_name,
    w.status as workspace_status,
    
    -- Computed fields
    CASE 
        WHEN aa.quality_score IS NOT NULL AND aa.quality_score >= 0.8 THEN 'ready'
        WHEN aa.quality_score IS NOT NULL AND aa.quality_score >= 0.6 THEN 'review'
        ELSE 'needs_improvement'
    END as asset_readiness_status,
    
    CASE 
        WHEN d.status = 'completed' AND d.overall_quality_score >= 0.8 THEN 'production_ready'
        WHEN d.status = 'completed' THEN 'completed_needs_review'
        WHEN d.status = 'in_progress' THEN 'in_progress'
        ELSE 'draft'
    END as deliverable_readiness_status

FROM asset_artifacts aa
FULL OUTER JOIN deliverables d ON aa.workspace_id = d.workspace_id
LEFT JOIN workspaces w ON COALESCE(aa.workspace_id, d.workspace_id) = w.id
WHERE 
    (aa.id IS NOT NULL OR d.id IS NOT NULL)
    AND w.status != 'archived';

-- =====================================================================
-- 2. VISTA AGGREGATA WORKSPACE DELIVERABLE METRICS  
-- =====================================================================
CREATE OR REPLACE VIEW workspace_deliverable_metrics AS
SELECT 
    w.id as workspace_id,
    w.name as workspace_name,
    w.status as workspace_status,
    
    -- Asset metrics
    COUNT(DISTINCT aa.id) as total_assets,
    COUNT(DISTINCT CASE WHEN aa.quality_score >= 0.8 THEN aa.id END) as ready_assets,
    COUNT(DISTINCT CASE WHEN aa.quality_score < 0.6 THEN aa.id END) as poor_quality_assets,
    ROUND(AVG(aa.quality_score)::numeric, 2) as avg_asset_quality,
    
    -- Deliverable metrics  
    COUNT(DISTINCT d.id) as total_deliverables,
    COUNT(DISTINCT CASE WHEN d.status = 'completed' THEN d.id END) as completed_deliverables,
    COUNT(DISTINCT CASE WHEN d.status = 'in_progress' THEN d.id END) as in_progress_deliverables,
    ROUND(AVG(d.overall_quality_score)::numeric, 2) as avg_deliverable_quality,
    
    -- Task completion metrics
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    ROUND(
        (COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END)::float / 
         NULLIF(COUNT(DISTINCT t.id), 0)) * 100, 1
    ) as task_completion_percentage,
    
    -- Readiness indicators
    CASE 
        WHEN COUNT(DISTINCT d.id) > 0 
             AND COUNT(DISTINCT CASE WHEN d.status = 'completed' AND d.overall_quality_score >= 0.8 THEN d.id END) = COUNT(DISTINCT d.id)
        THEN 'production_ready'
        WHEN COUNT(DISTINCT aa.id) > 0 
             AND COUNT(DISTINCT CASE WHEN aa.quality_score >= 0.8 THEN aa.id END) >= COUNT(DISTINCT aa.id) * 0.8
        THEN 'mostly_ready'
        ELSE 'needs_work'
    END as overall_readiness,
    
    -- Timestamps
    MAX(GREATEST(aa.updated_at, d.updated_at, t.updated_at)) as last_activity,
    MIN(LEAST(aa.created_at, d.created_at, t.created_at)) as first_activity

FROM workspaces w
LEFT JOIN asset_artifacts aa ON w.id = aa.workspace_id
LEFT JOIN deliverables d ON w.id = d.workspace_id  
LEFT JOIN tasks t ON w.id = t.workspace_id
WHERE w.status != 'archived'
GROUP BY w.id, w.name, w.status;

-- =====================================================================
-- 3. STORED PROCEDURE: EXTRACT WORKSPACE ASSETS  
-- =====================================================================
CREATE OR REPLACE FUNCTION extract_workspace_deliverable_assets(
    p_workspace_id UUID,
    p_quality_threshold FLOAT DEFAULT 0.6,
    p_limit INT DEFAULT 100
)
RETURNS TABLE(
    asset_id UUID,
    asset_name VARCHAR,
    asset_type VARCHAR,
    asset_content JSONB,
    quality_score FLOAT,
    readiness_status VARCHAR,
    extraction_method VARCHAR,
    source_task_id UUID,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    WITH ranked_assets AS (
        SELECT 
            aa.id,
            aa.name as name,
            aa.type as type,
            aa.content,
            aa.quality_score,
            CASE 
                WHEN aa.quality_score >= 0.8 THEN 'ready'
                WHEN aa.quality_score >= 0.6 THEN 'review'
                ELSE 'needs_improvement'
            END as readiness,
            'database_direct' as extraction_method,
            aa.task_id as source_task_id,
            aa.created_at,
            ROW_NUMBER() OVER (
                PARTITION BY aa.type 
                ORDER BY aa.quality_score DESC, aa.created_at DESC
            ) as rn
        FROM asset_artifacts aa
        WHERE aa.workspace_id = p_workspace_id
          AND aa.quality_score >= p_quality_threshold
          
        UNION ALL
        
        -- Extract from task results  
        SELECT 
            gen_random_uuid() as id,
            t.name || '_extracted' as name,
            'task_result' as type,
            t.result as content,
            COALESCE(
                (t.result->>'quality_score')::float, 
                CASE WHEN t.status = 'completed' THEN 0.7 ELSE 0.5 END
            ) as quality_score,
            CASE 
                WHEN t.status = 'completed' AND t.result IS NOT NULL THEN 'review'
                ELSE 'needs_improvement'  
            END as readiness,
            'task_result_extraction' as extraction_method,
            t.id as source_task_id,
            t.updated_at as created_at,
            ROW_NUMBER() OVER (ORDER BY t.updated_at DESC) as rn
        FROM tasks t
        WHERE t.workspace_id = p_workspace_id
          AND t.status = 'completed'
          AND t.result IS NOT NULL
          AND jsonb_typeof(t.result) = 'object'
          AND NOT EXISTS (
              SELECT 1 FROM asset_artifacts aa2 
              WHERE aa2.task_id = t.id
          )
    )
    SELECT 
        ra.id,
        ra.name,
        ra.type,
        ra.content,
        ra.quality_score,
        ra.readiness,
        ra.extraction_method,
        ra.source_task_id,
        ra.created_at
    FROM ranked_assets ra
    WHERE ra.rn <= 3  -- Max 3 per type
    ORDER BY ra.quality_score DESC, ra.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 4. STORED PROCEDURE: CREATE DELIVERABLE FROM ASSETS
-- =====================================================================
CREATE OR REPLACE FUNCTION create_deliverable_from_assets(
    p_workspace_id UUID,
    p_deliverable_name VARCHAR,
    p_deliverable_type VARCHAR DEFAULT 'comprehensive',
    p_min_quality_score FLOAT DEFAULT 0.7
)
RETURNS TABLE(
    deliverable_id UUID,
    assets_included INT,
    avg_quality_score FLOAT,
    creation_status VARCHAR,
    next_steps TEXT[]
) AS $$
DECLARE
    v_deliverable_id UUID;
    v_assets_count INT;
    v_avg_quality FLOAT;
    v_deliverable_content JSONB;
    v_next_steps TEXT[];
BEGIN
    -- Get ready assets for deliverable
    WITH ready_assets AS (
        SELECT * FROM extract_workspace_deliverable_assets(
            p_workspace_id, 
            p_min_quality_score, 
            50
        )
        WHERE readiness_status IN ('ready', 'review')
    ),
    deliverable_content AS (
        SELECT 
            COUNT(*) as asset_count,
            AVG(quality_score) as avg_quality,
            jsonb_agg(
                jsonb_build_object(
                    'asset_id', asset_id,
                    'name', asset_name,
                    'type', asset_type, 
                    'content', asset_content,
                    'quality_score', quality_score,
                    'source_task_id', source_task_id
                )
            ) as assets_data
        FROM ready_assets
    )
    SELECT asset_count, avg_quality, assets_data
    INTO v_assets_count, v_avg_quality, v_deliverable_content
    FROM deliverable_content;
    
    -- Create deliverable if we have assets
    IF v_assets_count > 0 THEN
        INSERT INTO deliverables (
            id, workspace_id, name, deliverable_type, status, completed_assets, overall_quality_score, 
            created_at, updated_at
        ) VALUES (
            gen_random_uuid(), p_workspace_id, p_deliverable_name, p_deliverable_type,
            CASE WHEN v_avg_quality >= 0.8 THEN 'completed' ELSE 'in_progress' END,
            jsonb_build_object(
                'assets', v_deliverable_content,
                'creation_method', 'database_aggregation',
                'creation_timestamp', NOW()
            ),
            v_avg_quality, NOW(), NOW()
        ) 
        RETURNING id INTO v_deliverable_id;
        
        -- Determine next steps
        v_next_steps := ARRAY[]::TEXT[];
        IF v_avg_quality < 0.8 THEN
            v_next_steps := v_next_steps || 'Review and improve asset quality scores';
        END IF;
        IF v_assets_count < 5 THEN
            v_next_steps := v_next_steps || 'Consider adding more assets for comprehensive deliverable';
        END IF;
        IF v_next_steps = ARRAY[]::TEXT[] THEN
            v_next_steps := ARRAY['Deliverable ready for client delivery'];
        END IF;
        
        RETURN QUERY SELECT 
            v_deliverable_id,
            v_assets_count,
            v_avg_quality,
            'success'::VARCHAR,
            v_next_steps;
    ELSE
        RETURN QUERY SELECT 
            NULL::UUID,
            0,
            0.0::FLOAT,
            'no_assets'::VARCHAR,
            ARRAY['No assets meet minimum quality threshold']::TEXT[];
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 5. INDICI PER PERFORMANCE
-- =====================================================================

-- Asset artifacts performance indexes
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_workspace_quality 
ON asset_artifacts(workspace_id, quality_score DESC) 
WHERE quality_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_asset_artifacts_type_quality
ON asset_artifacts(type, quality_score DESC)
WHERE quality_score >= 0.6;

CREATE INDEX IF NOT EXISTS idx_asset_artifacts_task
ON asset_artifacts(task_id)
WHERE task_id IS NOT NULL;

-- Deliverables performance indexes  
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_status_quality
ON deliverables(workspace_id, status, overall_quality_score DESC);

CREATE INDEX IF NOT EXISTS idx_deliverables_type_created
ON deliverables(deliverable_type, created_at DESC);

-- Tasks performance indexes for asset extraction
CREATE INDEX IF NOT EXISTS idx_tasks_completed_result 
ON tasks(workspace_id, status, updated_at DESC) 
WHERE status = 'completed' AND result IS NOT NULL;

-- =====================================================================
-- 6. TRIGGER: AUTO-UPDATE WORKSPACE METRICS
-- =====================================================================
CREATE OR REPLACE FUNCTION update_workspace_deliverable_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update workspace metadata with latest deliverable metrics
    UPDATE workspaces SET 
        metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
            'deliverable_metrics_updated', NOW(),
            'total_assets', (
                SELECT COUNT(*) FROM asset_artifacts 
                WHERE workspace_id = COALESCE(NEW.workspace_id, OLD.workspace_id)
            ),
            'total_deliverables', (
                SELECT COUNT(*) FROM deliverables 
                WHERE workspace_id = COALESCE(NEW.workspace_id, OLD.workspace_id)
            )
        )
    WHERE id = COALESCE(NEW.workspace_id, OLD.workspace_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to relevant tables
DROP TRIGGER IF EXISTS trg_update_workspace_metrics_assets ON asset_artifacts;
CREATE TRIGGER trg_update_workspace_metrics_assets
    AFTER INSERT OR UPDATE OR DELETE ON asset_artifacts
    FOR EACH ROW EXECUTE FUNCTION update_workspace_deliverable_metrics();

DROP TRIGGER IF EXISTS trg_update_workspace_metrics_deliverables ON deliverables;  
CREATE TRIGGER trg_update_workspace_metrics_deliverables
    AFTER INSERT OR UPDATE OR DELETE ON deliverables
    FOR EACH ROW EXECUTE FUNCTION update_workspace_deliverable_metrics();

-- =====================================================================
-- COMMENTS & DOCUMENTATION
-- =====================================================================
COMMENT ON VIEW unified_asset_deliverable_view IS 
'Vista unificata che combina asset_artifacts e deliverables con metriche di readiness calcolate automaticamente';

COMMENT ON VIEW workspace_deliverable_metrics IS 
'Metriche aggregate per workspace con indicatori di completezza e qualità per dashboard';

COMMENT ON FUNCTION extract_workspace_deliverable_assets IS 
'Estrae assets da workspace con ranking qualitativo e support per multiple sorgenti (direct + task results)';

COMMENT ON FUNCTION create_deliverable_from_assets IS 
'Crea deliverable aggregando assets di qualità con next steps automatici e business logic';

-- =====================================================================
-- DONE: Database-First Deliverable System Foundation Ready
-- =====================================================================