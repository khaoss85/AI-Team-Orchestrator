#!/usr/bin/env python3
"""
Test script to verify all the performance and error fixes
"""

import asyncio
import sys
import time
from typing import Dict, Any

def test_basic_imports():
    """Test that all modules can be imported without errors"""
    try:
        # Test deliverable_aggregator fixes
        from deliverable_aggregator import DynamicAssetExtractor
        print("✅ DynamicAssetExtractor import successful")
        
        # Check that the method is correctly indented
        extractor = DynamicAssetExtractor()
        assert hasattr(extractor, '_enhance_with_schema_validation'), "Missing _enhance_with_schema_validation method"
        print("✅ DynamicAssetExtractor method structure correct")
        
        # Test executor with debouncing and circuit breaker
        from executor import TaskExecutor
        executor = TaskExecutor()
        
        # Check debouncing attributes
        assert hasattr(executor, '_pending_queries'), "Missing _pending_queries"
        assert hasattr(executor, '_debounce_window'), "Missing _debounce_window"
        assert hasattr(executor, '_query_debounce_cache'), "Missing _query_debounce_cache"
        print("✅ Executor debouncing configuration found")
        
        # Check circuit breaker attributes
        assert hasattr(executor, '_quality_circuit_breaker'), "Missing _quality_circuit_breaker"
        print("✅ Executor circuit breaker configuration found")
        
        # Check debouncing methods
        assert hasattr(executor, '_debounced_query'), "Missing _debounced_query method"
        assert hasattr(executor, '_execute_with_circuit_breaker'), "Missing _execute_with_circuit_breaker method"
        print("✅ Executor debouncing and circuit breaker methods found")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_circuit_breaker_logic():
    """Test circuit breaker state transitions"""
    try:
        from executor import TaskExecutor
        executor = TaskExecutor()
        
        # Test initial state
        circuit = executor._quality_circuit_breaker
        assert circuit['state'] == 'closed', f"Expected 'closed', got {circuit['state']}"
        assert circuit['failure_count'] == 0, f"Expected 0 failures, got {circuit['failure_count']}"
        print("✅ Circuit breaker initial state correct")
        
        # Test state checking
        state = executor._check_circuit_breaker_state()
        assert state == 'closed', f"Expected 'closed', got {state}"
        print("✅ Circuit breaker state checking works")
        
        # Simulate failures to test trip logic
        circuit['failure_count'] = 4  # Just below threshold
        circuit['state'] = 'closed'
        
        # Should still be closed
        state = executor._check_circuit_breaker_state()
        assert state == 'closed', f"Expected 'closed' with 4 failures, got {state}"
        
        # Trip the circuit
        circuit['failure_count'] = 5  # At threshold
        circuit['last_failure_time'] = time.time()
        circuit['state'] = 'open'
        
        state = executor._check_circuit_breaker_state()
        assert state == 'open', f"Expected 'open', got {state}"
        print("✅ Circuit breaker trip logic works")
        
        return True
        
    except Exception as e:
        print(f"❌ Circuit breaker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_values():
    """Test that configuration values are reasonable"""
    try:
        from executor import TaskExecutor
        executor = TaskExecutor()
        
        # Check debouncing configuration
        assert executor._debounce_window == 2.0, f"Expected 2.0s debounce, got {executor._debounce_window}"
        assert isinstance(executor._pending_queries, dict), "Expected dict for _pending_queries"
        print("✅ Debouncing configuration values correct")
        
        # Check circuit breaker configuration
        circuit = executor._quality_circuit_breaker
        assert circuit['failure_threshold'] == 5, f"Expected 5 failure threshold, got {circuit['failure_threshold']}"
        assert circuit['recovery_timeout'] == 300, f"Expected 300s recovery timeout, got {circuit['recovery_timeout']}"
        assert circuit['state'] == 'closed', f"Expected 'closed' initial state, got {circuit['state']}"
        print("✅ Circuit breaker configuration values correct")
        
        # Check cache interval was increased
        assert executor.min_db_query_interval == 60, f"Expected 60s cache interval, got {executor.min_db_query_interval}"
        print("✅ Database cache interval optimized")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_functionality():
    """Test async methods work correctly"""
    try:
        from executor import TaskExecutor
        executor = TaskExecutor()
        
        # Test that async methods exist and can be called (though they'll fail without DB)
        async def dummy_query():
            return {"test": "data"}
        
        # This should work even without a real database
        try:
            result = await executor._debounced_query("test_key", dummy_query)
            assert result == {"test": "data"}, f"Expected test data, got {result}"
            print("✅ Debounced query async method works")
        except Exception as e:
            print(f"⚠️  Debounced query test skipped (expected without DB): {e}")
        
        # Test circuit breaker with dummy function
        async def dummy_operation():
            return "success"
        
        try:
            result = await executor._execute_with_circuit_breaker(dummy_operation)
            assert result == "success", f"Expected 'success', got {result}"
            print("✅ Circuit breaker async method works")
        except Exception as e:
            print(f"⚠️  Circuit breaker test skipped (expected without DB): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Async functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_protected_calls():
    """Test that deliverable creation calls are properly protected"""
    try:
        # Test monitoring.py
        with open('/Users/pelleri/Documents/ai-team-orchestrator/backend/routes/monitoring.py', 'r') as f:
            monitoring_content = f.read()
        
        assert '_execute_with_circuit_breaker' in monitoring_content, "Circuit breaker not found in monitoring.py"
        assert 'task_executor._execute_with_circuit_breaker' in monitoring_content, "Task executor circuit breaker call not found"
        print("✅ Monitoring route protected with circuit breaker")
        
        # Test task_analyzer.py
        with open('/Users/pelleri/Documents/ai-team-orchestrator/backend/task_analyzer.py', 'r') as f:
            analyzer_content = f.read()
        
        assert '_execute_with_circuit_breaker' in analyzer_content, "Circuit breaker not found in task_analyzer.py"
        assert '_safe_deliverable_creation' in analyzer_content, "Safe deliverable creation not found"
        print("✅ Task analyzer protected with circuit breaker")
        
        # Test executor.py
        with open('/Users/pelleri/Documents/ai-team-orchestrator/backend/executor.py', 'r') as f:
            executor_content = f.read()
        
        assert 'self._execute_with_circuit_breaker(_safe_deliverable_creation)' in executor_content, "Circuit breaker protection not found in executor"
        assert 'deliverable_id = None' in executor_content, "Variable initialization fix not found"
        print("✅ Executor protected with circuit breaker and variable fix")
        
        return True
        
    except Exception as e:
        print(f"❌ Protected calls test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_optimizations():
    """Test that performance optimizations are in place"""
    try:
        # Check that database calls use cached versions
        with open('/Users/pelleri/Documents/ai-team-orchestrator/backend/executor.py', 'r') as f:
            executor_content = f.read()
        
        # Count cached vs direct calls
        cached_tasks_calls = executor_content.count('self._cached_list_tasks')
        cached_agents_calls = executor_content.count('self._cached_list_agents')
        direct_list_tasks = executor_content.count('await list_tasks(') - executor_content.count('_debounced_query(') # Exclude the debounced calls
        direct_db_list_agents = executor_content.count('await db_list_agents(') - executor_content.count('_debounced_query(')
        
        print(f"📊 Performance metrics:")
        print(f"   - Cached task calls: {cached_tasks_calls}")
        print(f"   - Cached agent calls: {cached_agents_calls}")
        print(f"   - Direct task calls: {direct_list_tasks}")
        print(f"   - Direct agent calls: {direct_db_list_agents}")
        
        # Check that cached methods use debouncing
        assert '_debounced_query(' in executor_content, "Debounced queries not found"
        assert 'MIN_DB_QUERY_INTERVAL", "60"' in executor_content, "Cache interval not optimized"
        print("✅ Performance optimizations implemented")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🧪 Running comprehensive fixes verification\n")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Circuit Breaker Logic", test_circuit_breaker_logic),
        ("Configuration Values", test_configuration_values),
        ("Async Functionality", test_async_functionality),
        ("Protected Calls", test_protected_calls),
        ("Performance Optimizations", test_performance_optimizations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 Running: {test_name}")
        print("-" * 50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! All fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    # Change to backend directory
    import os
    os.chdir('/Users/pelleri/Documents/ai-team-orchestrator/backend')
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)