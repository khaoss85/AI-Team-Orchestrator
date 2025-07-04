# Service Registry for AI Team Orchestrator

**Generated**: 2025-07-03  
**Total Services**: 30  
**Status**: Active and maintained

## 🎯 Core System Services (Production Critical)

### Task Execution & Orchestration
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `adaptive_task_orchestration_engine.py` | Task optimization and skip rate management | executor.py, task_analyzer.py | 🟢 Active | Core System |
| `workflow_orchestrator.py` | Workflow coordination and management | executor.py, automated_goal_monitor.py | 🟢 Active | Orchestration |
| `dynamic_anti_loop_manager.py` | Loop prevention and reliability | executor.py | 🟢 Active | Reliability |

### Memory & Intelligence
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `memory_system.py` | Context storage, retrieval, insights | Multiple (core memory operations) | 🟢 Active | Memory |
| `thinking_process.py` | Real-time reasoning engine | executor.py, comprehensive_production_e2e_test.py | 🟢 Active | AI Core |
| `universal_ai_pipeline_engine.py` | Central AI operations hub | Multiple services | 🟢 Active | AI Core |

### Agent & Resource Management
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `agent_status_manager.py` | Agent coordination and status | executor.py, automated_goal_monitor.py | 🟢 Active | Agent Management |
| `workspace_health_manager.py` | Workspace health monitoring | executor.py, automated_goal_monitor.py | 🟢 Active | Monitoring |
| `system_telemetry_monitor.py` | System-wide monitoring | executor.py, routes/system_monitoring.py | 🟢 Active | Monitoring |

### Asset & Content Management
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `asset_requirements_generator.py` | Asset requirement generation | Multiple routes and systems | 🟢 Active | Asset System |
| `universal_ai_content_extractor.py` | Domain-agnostic content extraction | database.py, ai_driven_deliverable_system.py | 🟢 Active | Content |
| `document_manager.py` | Document handling operations | Multiple tools and routes | 🟢 Active | Document System |

## 🔧 Quality & Validation Services

### Quality Assurance
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `automatic_quality_trigger.py` | Automated quality validation triggers | Multiple integration points | 🟢 Active | Quality System |
| `ai_quality_gate_engine.py` | AI-driven quality gates | Asset system, tests | 🟢 Active | Quality System |
| `constraint_violation_preventer.py` | Database integrity protection | database.py | 🟢 Active | Database |

## 🚀 Specialized Services

### Asset Processing
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `asset_artifact_processor.py` | Asset artifact processing | Asset system integration | 🟢 Active | Asset System |
| `asset_driven_task_executor.py` | Asset-focused task execution | Asset system, monitoring | 🟢 Active | Asset System |
| `enhanced_goal_driven_planner.py` | Advanced goal planning | Asset system, tests | 🟢 Active | Planning |
| `memory_enhanced_ai_asset_generator.py` | Memory-aware asset generation | Database, pipeline integration | 🟡 Limited Use | Asset System |

### Deliverable & Achievement
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `asset_first_deliverable_system.py` | Asset-centric deliverable generation | deliverable_aggregator.py | 🟢 Active | Deliverable System |
| `deliverable_achievement_mapper.py` | Achievement to deliverable mapping | Database (conditional) | 🟡 Limited Use | Deliverable System |

### Pipeline & Integration
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `real_tool_integration_pipeline.py` | Real tool integration pipeline | Database (conditional) | 🟡 Limited Use | Tool Integration |
| `unified_progress_manager.py` | Cross-system progress tracking | Goal-driven planner, self-healing | 🟡 Limited Use | Progress Tracking |

## 🔍 Analysis & Validation Services

### Content Analysis
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `ai_resilient_similarity_engine.py` | Semantic similarity matching | Database, goal-driven planner | 🟡 Limited Use | AI Analysis |
| `ai_tool_aware_validator.py` | Tool-aware validation | Status unknown | 🔍 Needs Review | Validation |

### System Support
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `course_correction_engine.py` | Error recovery and correction | Test environments only | 🟡 Limited Use | Recovery |
| `quality_automation.py` | Automated quality processes | Test environments only | 🟡 Limited Use | Quality System |
| `task_deduplication_manager.py` | Task deduplication logic | Status unknown | 🔍 Needs Review | Task Management |

## 🧪 Experimental & Research Services

### Advanced Features
| Service | Purpose | Dependencies | Status | Owner |
|---------|---------|--------------|--------|-------|
| `goal_validation_optimizer.py` | Goal validation optimization | Status unknown | 🔍 Needs Review | Goal System |
| `universal_memory_architecture.py` | Advanced memory architecture | Status unknown | 🔍 Needs Review | Memory Research |
| `workspace_pause_manager.py` | Workspace pause/resume logic | Status unknown | 🔍 Needs Review | Workspace Management |

---

## 📊 Service Categories Summary

| Category | Count | Status |
|----------|-------|--------|
| 🟢 **Production Active** | 16 | Core system dependencies |
| 🟡 **Limited Use** | 8 | Conditional or specialized usage |
| 🔍 **Needs Review** | 6 | Usage verification required |
| **Total** | **30** | **All maintained** |

## 🔧 Service Management Guidelines

### Adding New Services
1. **Register here** - Add to appropriate category
2. **Document dependencies** - List all import relationships
3. **Assign ownership** - Designate responsible system/team
4. **Set status** - Mark as Active, Limited Use, or Review

### Deprecating Services
1. **Check dependencies** - Verify no active imports
2. **Migration plan** - Document replacement strategy
3. **Update registry** - Mark as deprecated before removal
4. **Archive safely** - Move to deprecated folder

### Monitoring Service Health
1. **Import tracking** - Monitor usage patterns
2. **Performance metrics** - Track execution and errors
3. **Dependency analysis** - Check for circular dependencies
4. **Regular audits** - Quarterly review of service usage

## 🔗 Key Integration Points

### Most Connected Services
1. **universal_ai_pipeline_engine.py** - Central hub for AI operations
2. **memory_system.py** - Core memory operations for multiple systems
3. **asset_requirements_generator.py** - Asset generation foundation
4. **automatic_quality_trigger.py** - Quality system integration

### Isolated Services (Review Candidates)
1. **ai_tool_aware_validator.py**
2. **goal_validation_optimizer.py** 
3. **task_deduplication_manager.py**
4. **workspace_pause_manager.py**
5. **universal_memory_architecture.py**

---

*This registry is automatically maintained and should be updated with any service changes.*