import { NextRequest, NextResponse } from 'next/server'

// Redirect map for removed routes
const ROUTE_REDIRECTS = {
  '/teams': '/projects',
  '/tools': '/projects', 
  '/knowledge': '/projects',
  '/settings': '/projects'
} as const

// Feature flags for gradual rollout
const FEATURE_FLAGS = {
  ENABLE_MINIMAL_SIDEBAR: process.env.NEXT_PUBLIC_ENABLE_MINIMAL_SIDEBAR === 'true',
  ENABLE_LEGACY_REDIRECTS: process.env.NEXT_PUBLIC_ENABLE_LEGACY_REDIRECTS !== 'false', // Default to true
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname
  
  // Handle legacy route redirects
  if (FEATURE_FLAGS.ENABLE_LEGACY_REDIRECTS) {
    const redirectPath = ROUTE_REDIRECTS[pathname as keyof typeof ROUTE_REDIRECTS]
    
    if (redirectPath) {
      console.log(`🔄 REDIRECT: ${pathname} → ${redirectPath}`)
      
      // Add deprecation headers
      const response = NextResponse.redirect(new URL(redirectPath, request.url))
      response.headers.set('X-Deprecated-Route', pathname)
      response.headers.set('X-Redirect-Reason', 'ui-simplification')
      response.headers.set('X-Migration-Date', '2025-09-03')
      
      return response
    }
  }
  
  // Continue to the requested page
  return NextResponse.next()
}

export const config = {
  matcher: [
    // Match the routes we want to handle
    '/teams',
    '/tools', 
    '/knowledge',
    '/settings',
    // Don't match API routes or static files
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}