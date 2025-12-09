// Proxy route to orchestrator for getting combat state (orchestrator proxies to combat agent)
export async function GET(
  req: Request,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params
    console.log('[Combat API] Fetching combat state for session:', sessionId)
    
    // Route through orchestrator (api-gateway) which has access to combat-agent
    const orchestratorUrl = process.env.ORCHESTRATOR_URL || 'http://api-gateway:8000'

    console.log('[Combat API] Calling orchestrator at:', `${orchestratorUrl}/combat/state/${sessionId}`)
    
    const response = await fetch(`${orchestratorUrl}/combat/state/${sessionId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Add timeout
      signal: AbortSignal.timeout(10000), // 10 second timeout
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('[Combat API] Orchestrator returned error:', response.status, errorText)
      let errorData = {}
      try {
        errorData = JSON.parse(errorText)
      } catch {
        errorData = { detail: errorText }
      }
      return Response.json(
        { 
          error: 'Failed to get combat state',
          detail: errorData.detail || `Orchestrator API returned ${response.status}`,
          status: response.status
        },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('[Combat API] Successfully loaded combat state:', data)
    return Response.json(data)
  } catch (error: any) {
    console.error('[Combat API] Failed to get combat state:', error)
    return Response.json(
      { 
        error: 'Failed to get combat state',
        detail: error.message || 'Unknown error',
        type: error.name
      },
      { status: 500 }
    )
  }
}

