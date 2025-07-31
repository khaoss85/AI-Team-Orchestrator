#!/usr/bin/env python3
"""
Alert System for AI Team Orchestrator
Sends notifications when critical issues are detected

Features:
- Email alerts for critical issues
- Slack notifications (configurable)
- Health report generation
- Escalation logic
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AlertSystem:
    """Handles alerting and notifications for system issues"""
    
    def __init__(self):
        # Email configuration (from environment)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('ALERT_EMAIL_USER')
        self.email_password = os.getenv('ALERT_EMAIL_PASSWORD')
        self.alert_recipients = os.getenv('ALERT_RECIPIENTS', '').split(',')
        
        # Alerting thresholds
        self.critical_health_threshold = int(os.getenv('CRITICAL_HEALTH_THRESHOLD', '30'))
        self.warning_health_threshold = int(os.getenv('WARNING_HEALTH_THRESHOLD', '70'))
        
        # Rate limiting to avoid spam
        self.last_critical_alert = None
        self.alert_cooldown_minutes = int(os.getenv('ALERT_COOLDOWN_MINUTES', '60'))
    
    def should_send_alert(self, severity: str) -> bool:
        """Check if we should send an alert based on rate limiting"""
        if severity != 'critical':
            return True
            
        if not self.last_critical_alert:
            return True
            
        # Check cooldown period
        time_since_last = datetime.now() - self.last_critical_alert
        return time_since_last.total_seconds() > (self.alert_cooldown_minutes * 60)
    
    def send_email_alert(self, subject: str, body: str, severity: str = 'warning'):
        """Send email alert"""
        if not self.email_user or not self.email_password or not self.alert_recipients:
            logger.warning("Email alerting not configured - skipping email")
            return False
            
        if not self.should_send_alert(severity):
            logger.info(f"Skipping {severity} alert due to rate limiting")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = ', '.join(self.alert_recipients)
            msg['Subject'] = f"[AI Orchestrator] {subject}"
            
            # Add severity indicator to body
            severity_emoji = {'critical': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}
            formatted_body = f"{severity_emoji.get(severity, '')} {body}"
            
            msg.attach(MIMEText(formatted_body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email alert sent: {subject}")
            
            if severity == 'critical':
                self.last_critical_alert = datetime.now()
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")
            return False
    
    def send_slack_alert(self, message: str, severity: str = 'warning'):
        """Send Slack alert (if configured)"""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        
        if not webhook_url:
            logger.debug("Slack webhook not configured - skipping Slack notification")
            return False
        
        try:
            import requests
            
            # Color coding based on severity
            color_map = {
                'critical': '#FF0000',  # Red
                'warning': '#FF8C00',   # Orange  
                'info': '#36A64F'       # Green
            }
            
            payload = {
                'attachments': [{
                    'color': color_map.get(severity, '#36A64F'),
                    'fields': [{
                        'title': 'AI Team Orchestrator Alert',
                        'value': message,
                        'short': False
                    }],
                    'footer': 'Health Monitor',
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Slack alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Slack alert: {e}")
            return False
    
    def process_health_results(self, health_results: Dict[str, Any]):
        """Process health check results and send appropriate alerts"""
        health_score = health_results.get('health_score', 0)
        issues = health_results.get('issues_found', [])
        fixes = health_results.get('fixes_applied', [])
        warnings = health_results.get('warnings', [])
        
        # Determine severity
        if health_score <= self.critical_health_threshold:
            severity = 'critical'
        elif health_score <= self.warning_health_threshold:
            severity = 'warning'
        else:
            severity = 'info'
        
        # Create alert message
        if severity == 'critical':
            subject = f"CRITICAL: System Health Score {health_score}/100"
            message = self._create_critical_alert_message(health_results)
        elif severity == 'warning' and (issues or len(warnings) > 2):
            subject = f"WARNING: System Health Issues Detected"
            message = self._create_warning_alert_message(health_results)
        elif fixes:
            subject = f"INFO: Auto-Fixes Applied"
            message = self._create_info_alert_message(health_results)
        else:
            # System is healthy, no alert needed
            return
        
        # Send alerts
        self.send_email_alert(subject, message, severity)
        self.send_slack_alert(message, severity)
        
        # Log alert
        logger.info(f"🚨 Alert sent - {severity.upper()}: {subject}")
    
    def _create_critical_alert_message(self, results: Dict[str, Any]) -> str:
        """Create critical alert message"""
        health_score = results['health_score']
        issues = results['issues_found']
        
        message = f"""CRITICAL SYSTEM HEALTH ALERT

Health Score: {health_score}/100
Timestamp: {results['timestamp']}

🚨 CRITICAL ISSUES DETECTED:
"""
        
        for issue in issues:
            message += f"• {issue}\n"
        
        message += f"""
IMMEDIATE ACTION REQUIRED:
1. Check system logs for detailed error information
2. Verify workspace and executor status
3. Restart services if necessary
4. Contact system administrator if issues persist

This is an automated alert from the AI Team Orchestrator health monitor.
"""
        
        return message
    
    def _create_warning_alert_message(self, results: Dict[str, Any]) -> str:
        """Create warning alert message"""
        health_score = results['health_score']
        issues = results['issues_found']
        warnings = results['warnings']
        fixes = results['fixes_applied']
        
        message = f"""System Health Warning

Health Score: {health_score}/100
Timestamp: {results['timestamp']}

"""
        
        if issues:
            message += "⚠️ ISSUES FOUND:\n"
            for issue in issues:
                message += f"• {issue}\n"
            message += "\n"
        
        if warnings:
            message += "📋 WARNINGS:\n"
            for warning in warnings:
                message += f"• {warning}\n"
            message += "\n"
        
        if fixes:
            message += "🔧 AUTOMATIC FIXES APPLIED:\n"
            for fix in fixes:
                message += f"• {fix}\n"
            message += "\n"
        
        message += "System is being monitored and auto-repaired where possible."
        
        return message
    
    def _create_info_alert_message(self, results: Dict[str, Any]) -> str:
        """Create info alert message"""
        fixes = results['fixes_applied']
        health_score = results['health_score']
        
        message = f"""System Auto-Repair Report

Health Score: {health_score}/100
Timestamp: {results['timestamp']}

🔧 AUTOMATIC FIXES APPLIED:
"""
        
        for fix in fixes:
            message += f"• {fix}\n"
        
        message += "\nSystem health has been automatically restored."
        
        return message
    
    def generate_daily_report(self, health_history: List[Dict[str, Any]]) -> str:
        """Generate daily health report"""
        if not health_history:
            return "No health data available for report."
        
        # Calculate statistics
        scores = [h['health_score'] for h in health_history]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        total_issues = sum(len(h.get('issues_found', [])) for h in health_history)
        total_fixes = sum(len(h.get('fixes_applied', [])) for h in health_history)
        total_warnings = sum(len(h.get('warnings', [])) for h in health_history)
        
        report = f"""AI Team Orchestrator - Daily Health Report
Date: {datetime.now().strftime('%Y-%m-%d')}

📊 HEALTH STATISTICS:
• Average Health Score: {avg_score:.1f}/100
• Minimum Health Score: {min_score}/100  
• Maximum Health Score: {max_score}/100
• Health Checks Performed: {len(health_history)}

🔧 MAINTENANCE STATISTICS:
• Total Issues Detected: {total_issues}
• Auto-Fixes Applied: {total_fixes}
• Warnings Generated: {total_warnings}

📈 SYSTEM STATUS:
"""
        
        if avg_score >= 90:
            report += "✅ EXCELLENT - System running optimally\n"
        elif avg_score >= 70:
            report += "✅ GOOD - System stable with minor issues\n"
        elif avg_score >= 50:
            report += "⚠️ NEEDS ATTENTION - Multiple issues detected\n"
        else:
            report += "🚨 CRITICAL - System requires immediate attention\n"
        
        # Recent issues
        recent_issues = []
        for h in health_history[-5:]:  # Last 5 checks
            recent_issues.extend(h.get('issues_found', []))
        
        if recent_issues:
            report += f"\n🔴 RECENT ISSUES:\n"
            for issue in set(recent_issues):  # Remove duplicates
                report += f"• {issue}\n"
        
        report += f"\nReport generated: {datetime.now().isoformat()}"
        
        return report

# Create singleton instance
alert_system = AlertSystem()