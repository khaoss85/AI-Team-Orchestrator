// Supabase Edge Function: submit-lead
// Based on existing backend endpoint /api/book-leads
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface LeadRequest {
  name: string
  email: string
  role?: string // ceo, cto, developer, manager, consultant, student, other
  challenge?: string
  gdpr_consent: boolean
  marketing_consent: boolean
  book_chapter?: string
  user_agent?: string
  referrer_url?: string
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    // Only allow POST
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }), 
        { status: 405, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Parse request body
    const leadData: LeadRequest = await req.json()
    
    // Validate required fields (same validation as backend)
    if (!leadData.name || !leadData.email || !leadData.gdpr_consent) {
      return new Response(
        JSON.stringify({ 
          success: false,
          error: 'Missing required fields: name, email, gdpr_consent' 
        }), 
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Email validation (same regex as backend models.py)
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    if (!emailRegex.test(leadData.email)) {
      return new Response(
        JSON.stringify({ 
          success: false,
          error: 'Email format not valid' 
        }), 
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Check if email already exists
    const { data: existingLead } = await supabase
      .from('book_leads')
      .select('id, confirmation_status, email')
      .eq('email', leadData.email.toLowerCase())
      .single()

    // If already confirmed, return success message
    if (existingLead && existingLead.confirmation_status === 'confirmed') {
      return new Response(
        JSON.stringify({ 
          success: true,
          message: 'Email già registrato e confermato! Riceverai gli aggiornamenti quando disponibili.',
          status: 'already_confirmed',
          lead_id: existingLead.id
        }), 
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Generate confirmation token
    const token = crypto.randomUUID()
    const tokenHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token))
    const hashArray = Array.from(new Uint8Array(tokenHash))
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
    
    // Token expires in 48 hours
    const expiresAt = new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString()

    // Get client info (same as backend)
    const userAgent = req.headers.get('user-agent') || leadData.user_agent || null
    const clientIP = req.headers.get('x-forwarded-for') || req.headers.get('x-real-ip') || null
    const referrerUrl = req.headers.get('referer') || leadData.referrer_url || null

    // Prepare lead record (matching backend structure)
    const leadRecord = {
      id: crypto.randomUUID(), // Generate UUID like backend
      name: leadData.name,
      email: leadData.email.toLowerCase(),
      role: leadData.role || null,
      challenge: leadData.challenge || null,
      gdpr_consent: leadData.gdpr_consent,
      marketing_consent: leadData.marketing_consent || false,
      book_chapter: leadData.book_chapter || 'chapter-2',
      user_agent: userAgent,
      ip_address: clientIP,
      referrer_url: referrerUrl,
      confirmation_status: 'pending',
      confirmation_token_hash: hashHex,
      confirmation_expires_at: expiresAt,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    // Insert or update lead
    const { data: lead, error: dbError } = await supabase
      .from('book_leads')
      .upsert(leadRecord, { 
        onConflict: 'email',
        ignoreDuplicates: false 
      })
      .select()
      .single()

    if (dbError) {
      console.error('Database error:', dbError)
      return new Response(
        JSON.stringify({ 
          success: false,
          error: 'Failed to save lead' 
        }), 
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Send confirmation email
    const bookUrl = Deno.env.get('BOOK_URL') || 'https://ai-team-orchestrator.com'
    const confirmationUrl = `${bookUrl}/api/book-leads/confirm?token=${token}&email=${encodeURIComponent(leadData.email)}`
    
    // Try to send email
    const emailSent = await sendConfirmationEmail(leadData.email, leadData.name, token, confirmationUrl)
    
    if (!emailSent) {
      console.warn(`Email sending failed for ${leadData.email}, but lead was saved`)
    }

    // Return success response (matching backend format)
    return new Response(
      JSON.stringify({ 
        success: true,
        message: emailSent 
          ? 'Confirmation email sent! Check your inbox and click the link to complete subscription.' 
          : 'Lead saved! Confirmation email could not be sent, but your information is recorded.',
        status: 'pending_confirmation',
        lead_id: lead.id
      }), 
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Function error:', error)
    return new Response(
      JSON.stringify({ 
        success: false,
        error: 'Internal server error' 
      }), 
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function sendConfirmationEmail(email: string, name: string, token: string, confirmationUrl: string): Promise<boolean> {
  try {
    const resendApiKey = Deno.env.get('RESEND_API_KEY')
    if (!resendApiKey) {
      console.warn('RESEND_API_KEY not configured')
      return false
    }

    const emailHtml = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #4c1d95, #d97706); color: white; padding: 30px 20px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
            .cta-button { display: inline-block; background: #d97706; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
            .footer { text-align: center; color: #666; font-size: 0.9rem; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 AI Team Orchestrator</h1>
            <p>Conferma la tua iscrizione</p>
        </div>
        <div class="content">
            <h2>Ciao ${name}! 👋</h2>
            <p>Grazie per il tuo interesse in <strong>"Building AI Team Orchestrators"</strong>!</p>
            <p>Per favore conferma il tuo indirizzo email per completare l'iscrizione:</p>
            <p style="text-align: center;">
                <a href="${confirmationUrl}" class="cta-button">
                    ✅ Conferma Iscrizione
                </a>
            </p>
            <p><em>Questo link scade tra 48 ore.</em></p>
            <p>Una volta confermata, riceverai:</p>
            <ul>
                <li>📚 Aggiornamenti su nuovi capitoli e contenuti</li>
                <li>🔍 Case study reali e war stories</li>
                <li>🛠️ Guide pratiche di implementazione</li>
                <li>💡 Insights sull'architettura AI</li>
            </ul>
        </div>
        <div class="footer">
            <p>Se non ti sei iscritto tu, puoi ignorare questa email.</p>
            <p>© 2025 Daniele Pelleri - AI Team Orchestrator</p>
        </div>
    </body>
    </html>
    `

    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${resendApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'AI Team Orchestrator <noreply@ai-team-orchestrator.com>', // Update with your domain
        to: [email],
        subject: '📚 Conferma la tua iscrizione ad AI Team Orchestrator',
        html: emailHtml
      }),
    })

    if (response.ok) {
      console.log(`Confirmation email sent to ${email}`)
      return true
    } else {
      console.error('Failed to send email:', await response.text())
      return false
    }

  } catch (error) {
    console.error('Email sending error:', error)
    return false
  }
}