"""
Asset System Test Suite - Comprehensive testing for asset-driven orchestration
Tests all components of the asset-driven system including services, API endpoints, and database operations.
"""

import pytest
import asyncio
import json
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, patch

# Import our asset system components
from services.asset_requirements_generator import AssetRequirementsGenerator
from services.asset_artifact_processor import AssetArtifactProcessor
from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
from deliverable_system.unified_deliverable_engine import unified_deliverable_engine as AssetDrivenTaskExecutor
from services.enhanced_goal_driven_planner import EnhancedGoalDrivenPlanner
from database_asset_extensions import AssetDrivenDatabaseManager

from models import (
    AssetRequirement, AssetArtifact, QualityValidation, QualityRule,
    WorkspaceGoal, EnhancedTask, TaskStatus
)

class TestAssetRequirementsGenerator:
    """Test suite for AssetRequirementsGenerator service"""
    
    @pytest.fixture
    def generator(self):
        return AssetRequirementsGenerator()
    
    @pytest.fixture
    def sample_goal(self):
        return WorkspaceGoal(
            id=uuid4(),
            workspace_id=uuid4(),
            metric_type="Customer Acquisition",
            target_value=100,
            current_value=0,
            progress_percentage=0,
            status="active",
            priority=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_generate_from_goal(self, generator, sample_goal):
        """Test AI-driven asset requirements generation"""
        with patch.object(generator.ai_pipeline_engine, 'execute_pipeline_step', new_callable=AsyncMock) as mock_execute_step:
            # Mock AI Pipeline response
            mock_pipeline_result = Mock()
            mock_pipeline_result.success = True
            mock_pipeline_result.data = {
                "response": "```json\n" + json.dumps({
                    "goal_analysis": {
                        "complexity_level": "medium",
                        "domain_category": "universal",
                        "estimated_completion_time": "2 weeks"
                    },
                    "asset_requirements": [
                        {
                            "asset_name": "Customer Acquisition Strategy Document",
                            "asset_type": "document",
                            "asset_format": "structured_data",
                            "description": "Comprehensive strategy for acquiring 100 customers",
                            "business_value_score": 0.9,
                            "actionability_score": 0.85,
                            "acceptance_criteria": {
                                "content_requirements": ["Market analysis", "Target personas"],
                                "quality_standards": ["Professional format", "Data-driven insights"],
                                "completion_criteria": ["Approved by stakeholders"]
                            },
                            "priority": "high",
                            "estimated_effort": "high",
                            "user_impact": "immediate",
                            "weight": 2.0,
                            "mandatory": True,
                            "value_proposition": "Clear roadmap for customer acquisition"
                        }
                    ]
                }) + "\n```"
            }
            mock_execute_step.return_value = mock_pipeline_result
            
            with patch.object(generator.db_manager, 'get_asset_requirements_for_goal', new_callable=AsyncMock) as mock_get_reqs:
                mock_get_reqs.return_value = [] # No existing requirements
                with patch.object(generator.db_manager, 'create_asset_requirement', new_callable=AsyncMock) as mock_create_req:
                    # The create method should return the same object it receives
                    mock_create_req.side_effect = lambda req: req

                    # Test generation
                    requirements = await generator.generate_from_goal(sample_goal)
                    
                    assert len(requirements) == 1
                    assert requirements[0].asset_name == "Customer Acquisition Strategy Document"
                    assert requirements[0].asset_type == "document"
                    assert requirements[0].business_value_score == 0.9
                    assert requirements[0].ai_generated == True
                    
                    # Verify AI pipeline was called
                    mock_execute_step.assert_called_once()
    
    


class TestAssetArtifactProcessor:
    """Test suite for AssetArtifactProcessor service"""
    
    @pytest.fixture
    def processor(self):
        return AssetArtifactProcessor()
    
    @pytest.fixture
    def sample_task(self):
        return EnhancedTask(
            id=uuid4(),
            workspace_id=uuid4(),
            name="Create customer research document",
            description="Research and compile customer insights",
            status=TaskStatus.COMPLETED,
            result="Comprehensive customer research analysis with 50 insights and 10 actionable recommendations."
        )
    
    @pytest.fixture
    def sample_requirement(self):
        return AssetRequirement(
            id=uuid4(),
            goal_id=uuid4(),
            workspace_id=uuid4(),
            asset_name="Customer Research Document",
            asset_type="document",
            asset_format="structured_data",
            description="Detailed customer research findings",
            business_value_score=0.8
        )
    
    @pytest.mark.asyncio
    async def test_process_task_output(self, processor, sample_task, sample_requirement):
        """Test processing task output into structured artifact"""
        with patch('services.asset_artifact_processor.AssetArtifactProcessor._structure_and_enhance_content', new_callable=AsyncMock) as mock_enhance:
            mock_enhance.return_value = {
                "artifact_name": "Customer Research Analysis Report",
                "enhanced_content": "# Customer Research Analysis...",
                "metadata": {}, "tags": [], "quality_score": 0.88,
                "business_value_score": 0.92, "actionability_score": 0.85
            }

            with patch('services.asset_artifact_processor.create_asset_artifact', new_callable=AsyncMock) as mock_create:
                mock_artifact = AssetArtifact(
                    id=uuid4(),
                    requirement_id=sample_requirement.id,
                    task_id=sample_task.id,
                    workspace_id=sample_task.workspace_id,
                    artifact_name="Customer Research Analysis Report",
                    artifact_type="document",
                    artifact_format="structured_data",
                    content="Enhanced content",
                    quality_score=0.88,
                    business_value_score=0.92,
                    actionability_score=0.85,
                    status="draft",
                    ai_enhanced=True
                )
                mock_create.return_value = mock_artifact
                
                artifact = await processor.process_task_output(sample_task, sample_requirement)
                
                assert artifact is not None
                assert artifact.artifact_name == "Customer Research Analysis Report"
                assert artifact.quality_score == 0.88
                assert artifact.ai_enhanced == True


class TestAIQualityGateEngine:
    """Test suite for AIQualityGateEngine service"""
    
    @pytest.fixture
    def quality_engine(self):
        return unified_quality_engine
    
    @pytest.fixture
    def sample_artifact(self):
        return AssetArtifact(
            id=uuid4(),
            requirement_id=uuid4(),
            workspace_id=uuid4(),
            artifact_name="Test Document",
            artifact_type="document",
            artifact_format="structured_data",
            content="This is a test document with some content for quality validation.",
            quality_score=0.0,
            status="draft"
        )
    
    @pytest.fixture
    def sample_quality_rule(self):
        return QualityRule(
            id=uuid4(),
            asset_type="document",
            rule_name="Content Completeness Check",
            ai_validation_prompt="Validate that the document is complete and comprehensive",
            validation_model="gpt-4o-mini",
            threshold_score=0.8,
            auto_learning_enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_validate_artifact_quality(self, quality_engine, sample_artifact):
        """Test comprehensive AI-driven quality validation"""
        with patch.object(quality_engine, 'client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "validation_passed": True,
                "quality_score": 0.87,
                "detailed_feedback": "Document meets quality standards with good structure and content",
                "ai_assessment": "Well-structured document with clear sections and actionable content",
                "quality_dimensions": {
                    "completeness_score": 0.90,
                    "accuracy_score": 0.85,
                    "relevance_score": 0.88,
                    "usability_score": 0.82,
                    "professional_standard_score": 0.89
                },
                "business_impact_analysis": "High business value with immediate actionability",
                "actionability_score": 0.85,
                "improvement_suggestions": ["Add more specific examples", "Include data visualizations"],
                "pillar_compliance": {
                    "compliant_pillars": ["concrete_deliverables", "ai_driven", "quality_gates"],
                    "compliance_score": 0.86
                }
            })
            
            mock_client.chat.completions.create.return_value = mock_response
            
            quality_decision = await quality_engine.validate_asset_quality(sample_artifact, sample_artifact.artifact_name, {})
            assert quality_decision.overall_score >= 0.0


from backend.deliverable_system.unified_deliverable_engine import unified_deliverable_engine

class TestUnifiedDeliverableEngine:
    """Test suite for the UnifiedDeliverableEngine"""
    
    @pytest.fixture
    def task_executor(self):
        return unified_deliverable_engine



class TestEnhancedGoalDrivenPlanner:
    """Test suite for EnhancedGoalDrivenPlanner service"""
    
    @pytest.fixture
    def planner(self):
        return EnhancedGoalDrivenPlanner()
    
    @pytest.fixture
    def sample_workspace_id(self):
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_generate_asset_driven_tasks(self, planner, sample_workspace_id):
        """Test asset-driven task generation"""
        mock_goal = WorkspaceGoal(
            id=uuid4(),
            workspace_id=sample_workspace_id,
            metric_type="Revenue Growth",
            target_value=1000000,
            current_value=0,
            progress_percentage=0,
            status="active",
            priority=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_requirement = AssetRequirement(
            id=uuid4(),
            goal_id=mock_goal.id,
            workspace_id=sample_workspace_id,
            asset_name="Test Requirement",
            asset_type="document",
            description="A test requirement"
        )
        mock_task = EnhancedTask(
            id=uuid4(),
            workspace_id=sample_workspace_id,
            name="Create test document",
            description="A test task",
            status=TaskStatus.PENDING
        )

        with patch('services.enhanced_goal_driven_planner.get_workspace_goals', new_callable=AsyncMock) as mock_get_goals:
            mock_get_goals.return_value = [mock_goal.model_dump()]

            with patch.object(planner.asset_db_manager, 'get_asset_requirements_for_goal', new_callable=AsyncMock) as mock_get_reqs:
                mock_get_reqs.return_value = []  # No existing requirements

                with patch.object(planner.requirements_generator, 'generate_from_goal', new_callable=AsyncMock) as mock_gen_reqs:
                    mock_gen_reqs.return_value = [mock_requirement]

                    with patch.object(planner, '_requirement_has_sufficient_progress', new_callable=AsyncMock) as mock_has_progress:
                        mock_has_progress.return_value = False

                        with patch.object(planner, '_generate_tasks_for_requirement', new_callable=AsyncMock) as mock_gen_tasks:
                            mock_gen_tasks.return_value = [mock_task]
                            
                            with patch.object(planner, '_apply_intelligent_prioritization', new_callable=AsyncMock) as mock_prioritize:
                                mock_prioritize.side_effect = lambda tasks, goal: tasks # Return tasks as is

                                tasks = await planner.generate_asset_driven_tasks(sample_workspace_id)
                                
                                assert len(tasks) == 1
                                assert tasks[0].name == "Create test document"
                                mock_get_goals.assert_called_once_with(sample_workspace_id)
                                mock_gen_reqs.assert_called_once()
                                mock_gen_tasks.assert_called_once()


class TestAssetDrivenDatabaseManager:
    """Test suite for AssetDrivenDatabaseManager"""
    
    @pytest.fixture
    def db_manager(self):
        return AssetDrivenDatabaseManager()
    
    @pytest.fixture
    def sample_requirement(self):
        return AssetRequirement(
            id=uuid4(),
            goal_id=uuid4(),
            workspace_id=uuid4(),
            asset_name="Test Requirement",
            asset_type="document",
            asset_format="structured_data",
            description="Test requirement description",
            business_value_score=0.8,
            ai_generated=True
        )
    
    @pytest.mark.asyncio
    async def test_health_check(self, db_manager):
        """Test database health check"""
        with patch.object(db_manager, 'supabase') as mock_supabase:
            mock_response = Mock()
            mock_response.data = [{"id": "test"}]
            mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
            
            health_status = await db_manager.health_check()
            
            assert "status" in health_status
            assert "checks" in health_status
            assert health_status["status"] in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_get_asset_system_metrics(self, db_manager):
        """Test asset system metrics retrieval"""
        workspace_id = uuid4()
        
        with patch.object(db_manager, 'supabase') as mock_supabase:
            # Mock requirements count
            req_response = Mock()
            req_response.count = 5
            
            # Mock artifacts data
            art_response = Mock()
            art_response.data = [
                {"status": "approved", "artifact_type": "document", "quality_score": 0.9},
                {"status": "approved", "artifact_type": "data", "quality_score": 0.8},
                {"status": "needs_improvement", "artifact_type": "document", "quality_score": 0.6}
            ]
            
            # Mock validations count
            val_response = Mock()
            val_response.count = 10
            
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = req_response
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
                req_response, art_response, val_response
            ]
            
            metrics = await db_manager.get_asset_system_metrics(workspace_id)
            
            assert "total_artifacts" in metrics
            assert "approved_artifacts" in metrics
            assert "avg_quality_score" in metrics
            assert "status_distribution" in metrics


class TestIntegrationScenarios:
    """Integration tests for complete asset-driven workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_asset_workflow(self):
        """Test complete workflow from goal to approved artifact"""
        # Setup
        workspace_id = uuid4()
        goal_id = uuid4()
        
        goal = WorkspaceGoal(
            id=goal_id,
            workspace_id=workspace_id,
            metric_type="Product Launch",
            target_value=1,
            current_value=0,
            progress_percentage=0,
            status="active",
            priority=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Step 1: Generate requirements
        generator = AssetRequirementsGenerator()
        with patch.object(generator.ai_pipeline_engine, 'execute_pipeline_step', new_callable=AsyncMock) as mock_execute_step:
            mock_pipeline_result = Mock()
            mock_pipeline_result.success = True
            mock_pipeline_result.data = {
                "response": "```json\n" + json.dumps({
                    "goal_analysis": {"complexity_level": "high"},
                    "asset_requirements": [{
                        "asset_name": "Product Launch Plan",
                        "asset_type": "document",
                        "asset_format": "structured_data",
                        "description": "Comprehensive product launch strategy",
                        "business_value_score": 0.9,
                        "actionability_score": 0.85,
                        "priority": "high",
                        "weight": 2.0,
                        "mandatory": True
                    }]
                }) + "\n```"
            }
            mock_execute_step.return_value = mock_pipeline_result
            
            with patch.object(generator.db_manager, 'get_asset_requirements_for_goal', new_callable=AsyncMock) as mock_get_reqs:
                mock_get_reqs.return_value = [] # No existing requirements
                with patch.object(generator.db_manager, 'create_asset_requirement', new_callable=AsyncMock) as mock_create_req:
                    mock_create_req.side_effect = lambda req: req
                    requirements = await generator.generate_from_goal(goal)
                    assert len(requirements) == 1
            
        # Step 2: Create task and process output
        task = EnhancedTask(
            id=uuid4(),
            workspace_id=workspace_id,
            name="Create product launch plan",
            description="Develop comprehensive launch strategy",
            status=TaskStatus.COMPLETED,
            result="Detailed product launch plan with timeline, marketing strategy, and success metrics."
        )
        
        processor = AssetArtifactProcessor()
        with patch('services.asset_artifact_processor.AssetArtifactProcessor._structure_and_enhance_content', new_callable=AsyncMock) as mock_enhance:
            mock_enhance.return_value = {
                "artifact_name": "Product Launch Strategic Plan",
                "enhanced_content": "# Product Launch Plan...",
                "quality_score": 0.92,
                "business_value_score": 0.95,
                "actionability_score": 0.88
            }
            
            with patch('services.asset_artifact_processor.create_asset_artifact', new_callable=AsyncMock) as mock_create:
                mock_artifact = AssetArtifact(
                    id=uuid4(),
                    requirement_id=requirements[0].id,
                    task_id=task.id,
                    workspace_id=workspace_id,
                    artifact_name="Product Launch Strategic Plan",
                    artifact_type="document",
                    quality_score=0.92,
                    status="draft",
                    ai_enhanced=True
                )
                mock_create.return_value = mock_artifact
                
                artifact = await processor.process_task_output(task, requirements[0])
                assert artifact.quality_score >= 0.8
                
        # Step 3: Quality validation
        quality_engine = unified_quality_engine
        with patch.object(quality_engine, '_ai_powered_evaluation', new_callable=AsyncMock) as mock_ai_eval:
            mock_ai_eval.return_value = (
                {
                    "concreteness": 0.9,
                    "actionability": 0.9,
                    "completeness": 0.9,
                    "business_value": 0.9
                },
                ["All good!"]
            )
            with patch.object(quality_engine, '_detect_fake_content', new_callable=AsyncMock) as mock_fake_detect:
                mock_fake_detect.return_value = {"has_fake_content": False}

                quality_decision = await quality_engine.validate_asset_quality(artifact, artifact.artifact_name, {})
                assert quality_decision.ready_for_use or quality_decision.overall_score >= 0.8
        
        print("✅ Complete asset workflow integration test passed")


# Performance and Load Tests
class TestPerformance:
    """Performance tests for asset system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_artifact_processing(self):
        """Test concurrent processing of multiple artifacts"""
        processor = AssetArtifactProcessor()
        
        # Create multiple tasks
        tasks = []
        requirements = []
        
        for i in range(5):
            task = EnhancedTask(
                id=uuid4(),
                workspace_id=uuid4(),
                name=f"Test task {i}",
                description=f"Test description {i}",
                status=TaskStatus.COMPLETED,
                result=f"Test result {i}"
            )
            
            requirement = AssetRequirement(
                id=uuid4(),
                goal_id=uuid4(),
                workspace_id=task.workspace_id,
                asset_name=f"Test Asset {i}",
                asset_type="document",
                asset_format="structured_data",
                description=f"Test requirement {i}",
                business_value_score=0.8
            )
            
            tasks.append(task)
            requirements.append(requirement)
        
        with patch('services.asset_artifact_processor.AssetArtifactProcessor._structure_and_enhance_content', new_callable=AsyncMock) as mock_enhance:
            mock_enhance.return_value = {
                "artifact_name": "Test Artifact",
                "enhanced_content": "Test content",
                "quality_score": 0.8
            }
            
            with patch('services.asset_artifact_processor.create_asset_artifact', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = AssetArtifact(
                    id=uuid4(),
                    requirement_id=uuid4(),
                    workspace_id=uuid4(),
                    artifact_name="Test",
                    artifact_type="document",
                    quality_score=0.8,
                    status="draft"
                )
                
                # Process concurrently
                start_time = datetime.utcnow()
                results = await asyncio.gather(*[
                    processor.process_task_output(task, req) 
                    for task, req in zip(tasks, requirements)
                ])
                end_time = datetime.utcnow()
                
                processing_time = (end_time - start_time).total_seconds()
                
                assert len(results) == 5
                assert all(result is not None for result in results)
                assert processing_time < 10  # Should complete within 10 seconds
                
                print(f"✅ Concurrent processing completed in {processing_time:.2f} seconds")


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])