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
from services.ai_quality_gate_engine import AIQualityGateEngine
from services.asset_driven_task_executor import AssetDrivenTaskExecutor
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
            status="active"
        )
    
    @pytest.mark.asyncio
    async def test_generate_from_goal(self, generator, sample_goal):
        """Test AI-driven asset requirements generation"""
        with patch.object(generator, 'openai_client') as mock_client:
            # Mock OpenAI response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
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
            })
            
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test generation
            requirements = await generator.generate_from_goal(sample_goal)
            
            assert len(requirements) == 1
            assert requirements[0].asset_name == "Customer Acquisition Strategy Document"
            assert requirements[0].asset_type == "document"
            assert requirements[0].business_value_score == 0.9
            assert requirements[0].ai_generated == True
            
            # Verify OpenAI was called
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_and_enhance_requirements(self, generator):
        """Test AI validation and enhancement of requirements"""
        sample_requirement = AssetRequirement(
            id=uuid4(),
            goal_id=uuid4(),
            workspace_id=uuid4(),
            asset_name="Test Document",
            asset_type="document",
            asset_format="structured_data",
            description="Test description",
            business_value_score=0.6,
            ai_generated=True
        )
        
        with patch.object(generator, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "validation_score": 0.85,
                "passed_validation": True,
                "enhancement_needed": True,
                "enhanced_requirement": {
                    "asset_name": "Enhanced Test Document",
                    "description": "Enhanced description with more specificity",
                    "business_value_score": 0.9
                }
            })
            
            mock_client.chat.completions.create.return_value = mock_response
            
            enhanced_requirements = await generator.validate_and_enhance_requirements([sample_requirement])
            
            assert len(enhanced_requirements) == 1
            assert enhanced_requirements[0].asset_name == "Enhanced Test Document"
            assert enhanced_requirements[0].business_value_score == 0.9


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
        with patch.object(processor, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "artifact_name": "Customer Research Analysis Report",
                "enhanced_content": "# Customer Research Analysis\n\n## Key Insights\n1. Primary customer segment prefers mobile experience\n2. Price sensitivity is moderate\n\n## Recommendations\n1. Develop mobile-first strategy\n2. Implement tiered pricing",
                "metadata": {
                    "word_count": 150,
                    "sections_count": 2,
                    "enhancement_applied": ["structured formatting", "actionable insights"],
                    "completion_percentage": 95.0
                },
                "tags": ["customer research", "analysis", "mobile strategy"],
                "quality_score": 0.88,
                "business_value_score": 0.92,
                "actionability_score": 0.85
            })
            
            mock_client.chat.completions.create.return_value = mock_response
            
            with patch('database_asset_extensions.create_asset_artifact') as mock_create:
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
        return AIQualityGateEngine()
    
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
        with patch.object(quality_engine, 'openai_client') as mock_client:
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
            
            with patch.object(quality_engine, '_get_quality_rules') as mock_rules:
                mock_rules.return_value = []  # No specific rules for this test
                
                quality_decision = await quality_engine.validate_artifact_quality(sample_artifact)
                
                assert quality_decision["status"] in ["approved", "needs_improvement", "requires_human_review"]
                assert "overall_score" in quality_decision
                assert quality_decision["overall_score"] >= 0.0


class TestAssetDrivenTaskExecutor:
    """Test suite for AssetDrivenTaskExecutor service"""
    
    @pytest.fixture
    def task_executor(self):
        return AssetDrivenTaskExecutor()
    
    @pytest.fixture
    def sample_task(self):
        return EnhancedTask(
            id=uuid4(),
            workspace_id=uuid4(),
            name="Create market analysis",
            description="Analyze market conditions and opportunities",
            status=TaskStatus.COMPLETED,
            result="Market analysis completed with 20 key insights"
        )
    
    @pytest.mark.asyncio
    async def test_enhance_task_execution(self, task_executor, sample_task):
        """Test asset-driven enhancement of task execution"""
        original_result = {
            "status": "completed",
            "execution_time": 120,
            "result": "Task completed successfully"
        }
        
        with patch.object(task_executor, '_run_asset_processing_pipeline') as mock_pipeline:
            mock_pipeline.return_value = {
                "artifacts_created": 2,
                "quality_validations": [{"score": 0.85, "passed": True}],
                "goal_updates": [{"goal_id": "test", "progress": 75.0}],
                "processing_steps": ["identifying_requirements", "processing_artifacts", "quality_validation"],
                "errors": []
            }
            
            enhanced_result = await task_executor.enhance_task_execution(sample_task, original_result)
            
            assert enhanced_result["status"] == "completed"
            assert "asset_driven_processing" in enhanced_result
            assert enhanced_result["artifacts_created"] == 2
            assert enhanced_result["asset_driven_processing"]["artifacts_created"] == 2
    
    @pytest.mark.asyncio
    async def test_health_check(self, task_executor):
        """Test health check functionality"""
        health_status = await task_executor.health_check()
        
        assert "status" in health_status
        assert "components" in health_status
        assert "configuration" in health_status
        assert health_status["status"] in ["healthy", "unhealthy", "degraded"]


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
        with patch('database_asset_extensions.get_workspace_goals') as mock_get_goals:
            mock_goal = WorkspaceGoal(
                id=uuid4(),
                workspace_id=sample_workspace_id,
                metric_type="Revenue Growth",
                target_value=1000000,
                current_value=0,
                progress_percentage=0,
                status="active"
            )
            mock_get_goals.return_value = [mock_goal]
            
            with patch.object(planner, '_generate_tasks_for_goal') as mock_gen_tasks:
                mock_task = EnhancedTask(
                    id=uuid4(),
                    workspace_id=sample_workspace_id,
                    name="Create revenue strategy document",
                    description="Develop comprehensive revenue growth strategy",
                    status=TaskStatus.PENDING,
                    ai_generated=True
                )
                mock_gen_tasks.return_value = [mock_task]
                
                tasks = await planner.generate_asset_driven_tasks(sample_workspace_id)
                
                assert len(tasks) == 1
                assert tasks[0].name == "Create revenue strategy document"
                assert tasks[0].ai_generated == True


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
            status="active"
        )
        
        # Step 1: Generate requirements
        generator = AssetRequirementsGenerator()
        with patch.object(generator, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
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
            })
            mock_client.chat.completions.create.return_value = mock_response
            
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
        with patch.object(processor, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "artifact_name": "Product Launch Strategic Plan",
                "enhanced_content": "# Product Launch Plan\n\n## Timeline\n- Phase 1: Market Research (Week 1-2)\n- Phase 2: Product Development (Week 3-8)\n- Phase 3: Marketing Campaign (Week 9-12)\n- Phase 4: Launch (Week 13)\n\n## Success Metrics\n- 1000 pre-orders\n- 50% market awareness\n- 25% customer acquisition",
                "quality_score": 0.92,
                "business_value_score": 0.95,
                "actionability_score": 0.88
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            with patch('database_asset_extensions.create_asset_artifact') as mock_create:
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
        quality_engine = AIQualityGateEngine()
        with patch.object(quality_engine, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "validation_passed": True,
                "quality_score": 0.92,
                "detailed_feedback": "Excellent strategic plan with clear timeline and measurable objectives"
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            quality_decision = await quality_engine.validate_artifact_quality(artifact)
            assert quality_decision.get("status") == "approved" or quality_decision.get("overall_score", 0) >= 0.8
        
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
        
        with patch.object(processor, 'openai_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "artifact_name": "Test Artifact",
                "enhanced_content": "Test content",
                "quality_score": 0.8
            })
            mock_client.chat.completions.create.return_value = mock_response
            
            with patch('database_asset_extensions.create_asset_artifact') as mock_create:
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