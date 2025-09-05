#!/bin/bash

# Staging Deployment 24-Hour Monitoring Script
# Branch: staging-performance-optimizations-20250905-152353

echo "======================================"
echo "🚀 STAGING DEPLOYMENT MONITOR"
echo "======================================"
echo "Start Time: $(date)"
echo "Branch: staging-performance-optimizations-20250905-152353"
echo ""

# Configuration
MONITORING_DURATION=86400  # 24 hours in seconds
CHECK_INTERVAL=300         # Check every 5 minutes
ALERT_THRESHOLD_MEMORY=500 # Alert if memory > 500MB
ALERT_THRESHOLD_RESPONSE=500 # Alert if response > 500ms

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Monitoring loop
START_TIME=$(date +%s)
END_TIME=$((START_TIME + MONITORING_DURATION))
CHECK_COUNT=0
ERROR_COUNT=0
WARNING_COUNT=0

# Create log file
LOG_FILE="staging_monitor_$(date +%Y%m%d_%H%M%S).log"

log_message() {
    echo "$1" | tee -a "$LOG_FILE"
}

check_health() {
    local health_status=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    if [ "$health_status" = "healthy" ]; then
        echo -e "${GREEN}✅ Health Check: PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ Health Check: FAILED${NC}"
        ((ERROR_COUNT++))
        return 1
    fi
}

check_memory() {
    local memory_usage=$(ps aux | grep "python3 main.py" | grep -v grep | awk '{sum+=$6} END {print sum/1024}')
    if (( $(echo "$memory_usage > $ALERT_THRESHOLD_MEMORY" | bc -l) )); then
        echo -e "${YELLOW}⚠️  Memory Usage: ${memory_usage}MB (HIGH)${NC}"
        ((WARNING_COUNT++))
        return 1
    else
        echo -e "${GREEN}✅ Memory Usage: ${memory_usage}MB${NC}"
        return 0
    fi
}

check_response_time() {
    local response_time=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8000/api/quota/status)
    local response_ms=$(echo "$response_time * 1000" | bc)
    
    if (( $(echo "$response_ms > $ALERT_THRESHOLD_RESPONSE" | bc -l) )); then
        echo -e "${YELLOW}⚠️  Response Time: ${response_ms}ms (SLOW)${NC}"
        ((WARNING_COUNT++))
        return 1
    else
        echo -e "${GREEN}✅ Response Time: ${response_ms}ms${NC}"
        return 0
    fi
}

check_websocket_connections() {
    local ws_count=$(lsof -i :8000 2>/dev/null | grep -i websocket | wc -l)
    if [ "$ws_count" -gt 100 ]; then
        echo -e "${RED}❌ WebSocket Connections: $ws_count (LEAK DETECTED)${NC}"
        ((ERROR_COUNT++))
        return 1
    else
        echo -e "${GREEN}✅ WebSocket Connections: $ws_count${NC}"
        return 0
    fi
}

check_polling_interval() {
    local interval_check=$(grep -r "30000" frontend/src/hooks/ 2>/dev/null | wc -l)
    if [ "$interval_check" -gt 0 ]; then
        echo -e "${GREEN}✅ Polling Interval: 30 seconds confirmed ($interval_check occurrences)${NC}"
        return 0
    else
        echo -e "${RED}❌ Polling Interval: Not optimized${NC}"
        ((ERROR_COUNT++))
        return 1
    fi
}

# Main monitoring loop
log_message "Starting 24-hour staging monitoring..."
log_message "======================================="

while [ $(date +%s) -lt $END_TIME ]; do
    ((CHECK_COUNT++))
    
    echo ""
    log_message "=== Check #$CHECK_COUNT - $(date) ==="
    
    # Run all checks
    check_health
    check_memory
    check_response_time
    check_websocket_connections
    check_polling_interval
    
    # Summary for this check
    echo ""
    echo "Status: Errors=$ERROR_COUNT, Warnings=$WARNING_COUNT"
    
    # Alert if critical issues
    if [ $ERROR_COUNT -gt 5 ]; then
        echo -e "${RED}🚨 CRITICAL: Multiple errors detected! Consider rollback.${NC}"
        log_message "CRITICAL ALERT at $(date): $ERROR_COUNT errors detected"
    fi
    
    # Calculate remaining time
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    REMAINING=$((END_TIME - CURRENT_TIME))
    HOURS_REMAINING=$((REMAINING / 3600))
    
    echo "Progress: $(($ELAPSED * 100 / $MONITORING_DURATION))% complete"
    echo "Time remaining: $HOURS_REMAINING hours"
    echo "========================================="
    
    # Wait for next check
    sleep $CHECK_INTERVAL
done

# Final report
log_message ""
log_message "======================================"
log_message "📊 FINAL MONITORING REPORT"
log_message "======================================"
log_message "End Time: $(date)"
log_message "Total Checks: $CHECK_COUNT"
log_message "Total Errors: $ERROR_COUNT"
log_message "Total Warnings: $WARNING_COUNT"

if [ $ERROR_COUNT -eq 0 ] && [ $WARNING_COUNT -lt 10 ]; then
    log_message "✅ RESULT: Staging deployment PASSED validation"
    log_message "Ready for production deployment consideration"
    exit 0
else
    log_message "❌ RESULT: Staging deployment FAILED validation"
    log_message "Errors: $ERROR_COUNT, Warnings: $WARNING_COUNT"
    log_message "Review required before production deployment"
    exit 1
fi