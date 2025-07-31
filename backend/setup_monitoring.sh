#!/bin/bash

# Setup Monitoring for AI Team Orchestrator
# This script sets up automated monitoring and alerting

echo "🏥 Setting up AI Team Orchestrator Health Monitoring"
echo "=================================================="

# Get the current directory
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

echo "Backend directory: $BACKEND_DIR"
echo "Python path: $PYTHON_PATH"

# Make health monitor executable
chmod +x "$BACKEND_DIR/health_monitor.py"
echo "✅ Made health_monitor.py executable"

# Create logs directory if it doesn't exist
mkdir -p "$BACKEND_DIR/logs"
echo "✅ Created logs directory"

# Create monitoring script wrapper
cat > "$BACKEND_DIR/run_health_check.sh" << EOF
#!/bin/bash
cd "$BACKEND_DIR"
export PYTHONPATH="$BACKEND_DIR:\$PYTHONPATH"
source .env 2>/dev/null || true
$PYTHON_PATH health_monitor.py >> logs/health_monitor.log 2>&1
EOF

chmod +x "$BACKEND_DIR/run_health_check.sh"
echo "✅ Created health check wrapper script"

# Create daily report script
cat > "$BACKEND_DIR/run_daily_report.sh" << EOF
#!/bin/bash
cd "$BACKEND_DIR"  
export PYTHONPATH="$BACKEND_DIR:\$PYTHONPATH"
source .env 2>/dev/null || true
$PYTHON_PATH health_monitor.py --report >> logs/daily_reports.log 2>&1
EOF

chmod +x "$BACKEND_DIR/run_daily_report.sh"
echo "✅ Created daily report script"

# Check if crontab exists and backup
if crontab -l >/dev/null 2>&1; then
    echo "📋 Backing up existing crontab..."
    crontab -l > "$BACKEND_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
fi

# Add cron jobs
echo "⏰ Setting up cron jobs..."

# Create temporary crontab file
TEMP_CRON=$(mktemp)

# Add existing crontab (if any)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Add health monitoring jobs
cat >> "$TEMP_CRON" << EOF

# AI Team Orchestrator Health Monitoring
# Run health check every 5 minutes
*/5 * * * * $BACKEND_DIR/run_health_check.sh

# Generate daily report at 9 AM
0 9 * * * $BACKEND_DIR/run_daily_report.sh

# Clean old logs weekly (keep last 30 days)
0 2 * * 0 find $BACKEND_DIR/logs -name "*.log" -mtime +30 -delete

EOF

# Install new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Cron jobs installed successfully"

# Show installed cron jobs
echo ""
echo "📋 Installed cron jobs:"
crontab -l | grep -A 10 "AI Team Orchestrator"

# Create environment template for alerting
cat > "$BACKEND_DIR/.env.monitoring" << 'EOF'
# Health Monitoring Configuration
ENABLE_HEALTH_MONITOR=true
CRITICAL_HEALTH_THRESHOLD=30
WARNING_HEALTH_THRESHOLD=70
ALERT_COOLDOWN_MINUTES=60

# Email Alerting (optional)
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# ALERT_EMAIL_USER=your-email@gmail.com
# ALERT_EMAIL_PASSWORD=your-app-password
# ALERT_RECIPIENTS=admin@yourcompany.com,dev@yourcompany.com

# Slack Alerting (optional)
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
EOF

echo "✅ Created monitoring environment template"

# Test health monitor
echo ""
echo "🧪 Testing health monitor..."
cd "$BACKEND_DIR"
if source .env 2>/dev/null && python3 health_monitor.py; then
    echo "✅ Health monitor test passed"
else
    echo "⚠️ Health monitor test failed - check configuration"
fi

echo ""
echo "🎉 MONITORING SETUP COMPLETE!"
echo ""
echo "📋 What was installed:"
echo "   • Health monitor running every 5 minutes"
echo "   • Daily reports generated at 9 AM"  
echo "   • Log cleanup weekly"
echo "   • Health monitor integrated into main.py startup"
echo ""
echo "📧 To enable email/Slack alerts:"
echo "   1. Copy .env.monitoring to .env (or merge with existing .env)"
echo "   2. Configure SMTP and/or Slack webhook settings"  
echo "   3. Restart the application"
echo ""
echo "📊 To check system health manually:"
echo "   • Run: ./health_monitor.py"
echo "   • For detailed report: ./health_monitor.py --report"
echo ""
echo "📂 Logs location: $BACKEND_DIR/logs/"
echo "   • health_monitor.log - Health check logs"
echo "   • daily_reports.log - Daily health reports"