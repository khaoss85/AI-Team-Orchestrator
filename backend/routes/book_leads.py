"""
Book Leads Routes with Double Opt-in Support
"""
import os
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request, Query, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

router = APIRouter()

class ConfirmLeadRequest(BaseModel):
    token: str
    email: str

async def send_confirmation_email(email: str, name: str, token: str) -> bool:
    """Send confirmation email using Resend or fallback method"""
    try:
        # Check if we have Resend configured
        resend_api_key = os.getenv('RESEND_API_KEY')
        
        if not resend_api_key:
            logging.warning("RESEND_API_KEY not configured, skipping email")
            return True  # Return True to not block the flow
        
        import httpx
        
        # Get base URL for confirmation link
        base_url = os.getenv('BOOK_URL', 'https://ai-team-orchestrator.com')
        confirmation_url = f"{base_url}/api/book-leads/confirm?token={token}&email={email}"
        
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4c1d95, #d97706); color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .cta-button {{ display: inline-block; background: #d97706; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 0.9rem; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 AI Team Orchestrator</h1>
                <p>Confirm your subscription</p>
            </div>
            <div class="content">
                <h2>Hi {name}! 👋</h2>
                <p>Thanks for your interest in <strong>"Building AI Team Orchestrators"</strong>!</p>
                <p>Please confirm your email address to complete the subscription:</p>
                <p style="text-align: center;">
                    <a href="{confirmation_url}" class="cta-button">
                        ✅ Confirm Subscription
                    </a>
                </p>
                <p><em>This link expires in 48 hours.</em></p>
                <p>Once confirmed, you'll receive:</p>
                <ul>
                    <li>📚 Updates on new chapters and content</li>
                    <li>🔍 Real-world case studies and war stories</li>
                    <li>🛠️ Practical implementation guides</li>
                    <li>💡 AI architecture insights</li>
                </ul>
            </div>
            <div class="footer">
                <p>If you didn't sign up for this, you can safely ignore this email.</p>
                <p>© 2025 Daniele Pelleri - AI Team Orchestrator</p>
            </div>
        </body>
        </html>
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {resend_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'from': 'AI Team Orchestrator <noreply@yourdomain.com>',  # Update with your domain
                    'to': [email],
                    'subject': '📚 Confirm your AI Team Orchestrator subscription',
                    'html': email_html
                }
            )
            
            if response.status_code == 200:
                logging.info(f"Confirmation email sent to {email}")
                return True
            else:
                logging.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logging.error(f"Email sending error: {e}")
        return False

@router.get("/book-leads/confirm")
async def confirm_lead(token: str = Query(...), email: str = Query(...)):
    """Confirm lead subscription via email link"""
    try:
        from database import get_supabase_client
        
        # Hash the provided token to compare with stored hash
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        supabase = get_supabase_client()
        if not supabase:
            return HTMLResponse(
                content=get_error_html("Database connection failed"),
                status_code=500
            )
        
        # Find lead with matching email and token hash
        result = supabase.table("book_leads")\
            .select("*")\
            .eq("email", email)\
            .eq("confirmation_token_hash", token_hash)\
            .single()\
            .execute()
        
        if not result.data:
            return HTMLResponse(
                content=get_error_html("Invalid or expired confirmation link"),
                status_code=400
            )
        
        lead = result.data
        
        # Check if token has expired
        if lead.get('confirmation_expires_at'):
            expires_at = datetime.fromisoformat(lead['confirmation_expires_at'].replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) > expires_at:
                return HTMLResponse(
                    content=get_error_html("Confirmation link has expired (48 hours limit)"),
                    status_code=400
                )
        
        # Check if already confirmed
        if lead.get('confirmation_status') == 'confirmed':
            return HTMLResponse(
                content=get_success_html(lead['name'], already_confirmed=True),
                status_code=200
            )
        
        # Confirm the lead
        update_result = supabase.table("book_leads")\
            .update({
                "confirmation_status": "confirmed",
                "confirmed_at": datetime.utcnow().isoformat(),
                "confirmation_token_hash": None,  # Clear token after confirmation
                "confirmation_expires_at": None
            })\
            .eq("id", lead['id'])\
            .execute()
        
        if not update_result.data:
            return HTMLResponse(
                content=get_error_html("Failed to confirm subscription"),
                status_code=500
            )
        
        # Success!
        return HTMLResponse(
            content=get_success_html(lead['name']),
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Confirmation error: {e}")
        return HTMLResponse(
            content=get_error_html("An unexpected error occurred"),
            status_code=500
        )

def get_error_html(message: str) -> str:
    """Generate error HTML page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Confirmation Error</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                text-align: center; 
                padding: 50px; 
                line-height: 1.6;
                background: linear-gradient(135deg, #f8f9fa, #e2e8f0);
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            .error {{ color: #dc3545; }}
            .emoji {{ font-size: 3rem; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">❌</div>
            <h1 class="error">Confirmation Error</h1>
            <p>{message}</p>
            <p>Please try requesting a new confirmation email or contact support.</p>
        </div>
    </body>
    </html>
    """

def get_success_html(name: str, already_confirmed: bool = False) -> str:
    """Generate success HTML page"""
    book_url = os.getenv('BOOK_URL', 'https://ai-team-orchestrator.com')
    
    if already_confirmed:
        title = "Already Confirmed!"
        message = f"Hi {name}, your subscription is already active."
        emoji = "✅"
    else:
        title = "Subscription Confirmed!"
        message = f"Welcome aboard, {name}! Your subscription is now active."
        emoji = "🎉"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                text-align: center; 
                padding: 50px; 
                line-height: 1.6;
                background: linear-gradient(135deg, #f8f9fa, #e2e8f0);
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            .success {{ color: #28a745; }}
            .emoji {{ font-size: 3rem; margin: 20px 0; }}
            .cta {{ 
                display: inline-block; 
                background: #d97706; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: bold; 
                margin: 20px 0;
                transition: background 0.3s ease;
            }}
            .cta:hover {{ background: #b45309; }}
            .feature {{ margin: 10px 0; color: #666; }}
        </style>
        <script>
            // Auto-redirect after 5 seconds
            setTimeout(() => {{
                window.location.href = '{book_url}?confirmed=true';
            }}, 5000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="emoji">{emoji}</div>
            <h1 class="success">{title}</h1>
            <p>{message}</p>
            
            <div style="margin: 30px 0;">
                <div class="feature">📚 New chapters and content updates</div>
                <div class="feature">🔍 Real-world case studies</div>
                <div class="feature">🛠️ Practical implementation guides</div>
                <div class="feature">💡 AI architecture insights</div>
            </div>
            
            <a href="{book_url}?confirmed=true" class="cta">Continue Reading →</a>
            
            <p style="margin-top: 30px; color: #666; font-size: 0.9rem;">
                Redirecting in 5 seconds...
            </p>
        </div>
    </body>
    </html>
    """