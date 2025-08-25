// Supabase Edge Function: confirm-lead  
// Handles the confirmation link from email
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  try {
    // Only allow GET
    if (req.method !== 'GET') {
      return new Response('Method not allowed', { status: 405 })
    }

    // Parse URL parameters
    const url = new URL(req.url)
    const token = url.searchParams.get('token')
    const email = url.searchParams.get('email')

    if (!token || !email) {
      return new Response(getErrorHtml('Invalid confirmation link', 'The confirmation link is missing required parameters.'), { 
        status: 400, 
        headers: { 'Content-Type': 'text/html' } 
      })
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Hash the provided token to compare with stored hash
    const tokenHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token))
    const hashArray = Array.from(new Uint8Array(tokenHash))
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')

    // Find lead with matching email and token hash
    const { data: lead, error: dbError } = await supabase
      .from('book_leads')
      .select('*')
      .eq('email', email.toLowerCase())
      .eq('confirmation_token_hash', hashHex)
      .single()

    if (dbError || !lead) {
      return new Response(getErrorHtml('Invalid or expired token', 'This confirmation link is invalid or has expired. Please request a new confirmation email.'), { 
        status: 400, 
        headers: { 'Content-Type': 'text/html' } 
      })
    }

    // Check if token has expired
    if (lead.confirmation_expires_at) {
      const expiresAt = new Date(lead.confirmation_expires_at)
      const now = new Date()
      
      if (now > expiresAt) {
        return new Response(getErrorHtml('Token expired', 'This confirmation link has expired (48 hours limit). Please request a new confirmation email.'), { 
          status: 400, 
          headers: { 'Content-Type': 'text/html' } 
        })
      }
    }

    // Check if already confirmed
    if (lead.confirmation_status === 'confirmed') {
      return new Response(getSuccessHtml(lead.name, true), { 
        status: 200, 
        headers: { 'Content-Type': 'text/html' } 
      })
    }

    // Confirm the lead
    const { error: updateError } = await supabase
      .from('book_leads')
      .update({
        confirmation_status: 'confirmed',
        confirmed_at: new Date().toISOString(),
        confirmation_token_hash: null, // Clear token after confirmation
        confirmation_expires_at: null,
        updated_at: new Date().toISOString()
      })
      .eq('id', lead.id)

    if (updateError) {
      console.error('Update error:', updateError)
      return new Response(getErrorHtml('Confirmation failed', 'An error occurred while confirming your subscription. Please try again or contact support.'), { 
        status: 500, 
        headers: { 'Content-Type': 'text/html' } 
      })
    }

    // Success!
    return new Response(getSuccessHtml(lead.name, false), { 
      status: 200, 
      headers: { 'Content-Type': 'text/html' } 
    })

  } catch (error) {
    console.error('Confirmation error:', error)
    return new Response(getErrorHtml('Server error', 'An unexpected error occurred. Please try again later.'), { 
      status: 500, 
      headers: { 'Content-Type': 'text/html' } 
    })
  }
})

function getErrorHtml(title: string, message: string): string {
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <title>${title}</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                text-align: center; 
                padding: 50px; 
                line-height: 1.6;
                background: linear-gradient(135deg, #f8f9fa, #e2e8f0);
            }
            .container { 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            .error { color: #dc3545; }
            .emoji { font-size: 3rem; margin: 20px 0; }
            .cta { 
                display: inline-block; 
                background: #6c757d; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: bold; 
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">❌</div>
            <h1 class="error">${title}</h1>
            <p>${message}</p>
            <a href="${Deno.env.get('BOOK_URL') || 'https://ai-team-orchestrator.com'}" class="cta">← Torna al Libro</a>
        </div>
    </body>
    </html>
  `
}

function getSuccessHtml(name: string, alreadyConfirmed: boolean): string {
  const bookUrl = Deno.env.get('BOOK_URL') || 'https://ai-team-orchestrator.com'
  
  const title = alreadyConfirmed ? 'Già confermato!' : 'Iscrizione confermata!'
  const message = alreadyConfirmed 
    ? `Ciao ${name}, la tua iscrizione è già attiva.`
    : `Benvenuto a bordo, ${name}! La tua iscrizione è ora attiva.`
  const emoji = alreadyConfirmed ? '✅' : '🎉'
  
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <title>${title}</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                text-align: center; 
                padding: 50px; 
                line-height: 1.6;
                background: linear-gradient(135deg, #f8f9fa, #e2e8f0);
            }
            .container { 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            .success { color: #28a745; }
            .emoji { font-size: 3rem; margin: 20px 0; }
            .cta { 
                display: inline-block; 
                background: #d97706; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: bold; 
                margin: 20px 0;
                transition: background 0.3s ease;
            }
            .cta:hover { background: #b45309; }
            .feature { margin: 10px 0; color: #666; }
        </style>
        <script>
            // Auto-redirect after 5 seconds
            setTimeout(() => {
                window.location.href = '${bookUrl}?confirmed=true';
            }, 5000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="emoji">${emoji}</div>
            <h1 class="success">${title}</h1>
            <p>${message}</p>
            
            <div style="margin: 30px 0;">
                <div class="feature">📚 Aggiornamenti su nuovi capitoli e contenuti</div>
                <div class="feature">🔍 Case study reali e war stories</div>
                <div class="feature">🛠️ Guide pratiche di implementazione</div>
                <div class="feature">💡 Insights sull'architettura AI</div>
            </div>
            
            <a href="${bookUrl}?confirmed=true" class="cta">Continua a Leggere →</a>
            
            <p style="margin-top: 30px; color: #666; font-size: 0.9rem;">
                Reindirizzamento automatico in 5 secondi...
            </p>
        </div>
    </body>
    </html>
  `
}