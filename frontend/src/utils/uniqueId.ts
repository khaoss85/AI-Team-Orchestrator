/**
 * Utility for generating guaranteed unique IDs for React components and artifacts
 * Prevents React key duplicate warnings by ensuring no two IDs are ever the same
 */

// Counter to ensure uniqueness even within the same millisecond
let idCounter = 0

/**
 * Generates a unique ID for artifacts and React keys
 * Combines timestamp, counter, and random string to guarantee uniqueness
 * 
 * @param prefix - Optional prefix for the ID (e.g., 'tools', 'user', 'msg')
 * @returns A guaranteed unique ID string
 */
export function generateUniqueId(prefix?: string): string {
  // Increment counter for this session
  idCounter++
  
  // Get high-precision timestamp
  const timestamp = Date.now()
  
  // Generate random component (36 = 0-9 + a-z)
  const random = Math.random().toString(36).substring(2, 9)
  
  // Combine all components for guaranteed uniqueness
  // Format: prefix-timestamp-counter-random
  const components = [
    prefix,
    timestamp,
    idCounter,
    random
  ].filter(Boolean) // Remove undefined prefix if not provided
  
  return components.join('-')
}

/**
 * Generates a unique ID specifically for artifact objects
 * Includes the artifact type in the ID for better debugging
 * 
 * @param artifactType - Type of artifact ('tools', 'deliverable', 'progress', etc.)
 * @returns A unique artifact ID
 */
export function generateArtifactId(artifactType: string): string {
  return generateUniqueId(artifactType)
}

/**
 * Generates a unique ID for messages
 * 
 * @param messageType - Type of message ('user', 'ai', 'system')
 * @returns A unique message ID
 */
export function generateMessageId(messageType: string): string {
  return generateUniqueId(messageType)
}

/**
 * Validates that an array of objects has unique IDs
 * Useful for debugging React key issues
 * 
 * @param items - Array of objects with 'id' property
 * @returns Object with validation result and duplicate IDs if any
 */
export function validateUniqueIds<T extends { id: string }>(items: T[]): {
  isValid: boolean
  duplicates: string[]
} {
  const idMap = new Map<string, number>()
  const duplicates: string[] = []
  
  items.forEach(item => {
    const count = idMap.get(item.id) || 0
    idMap.set(item.id, count + 1)
    
    if (count === 1) {
      // This is the second occurrence, add to duplicates
      duplicates.push(item.id)
    }
  })
  
  return {
    isValid: duplicates.length === 0,
    duplicates
  }
}