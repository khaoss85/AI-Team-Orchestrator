import '@testing-library/jest-dom'

// Mock WebSocket for testing
global.WebSocket = class MockWebSocket {
  constructor(url) {
    this.url = url
    this.readyState = 1 // OPEN
    setTimeout(() => {
      if (this.onopen) this.onopen({})
    }, 10)
  }
  
  send(data) {
    // Mock send implementation
  }
  
  close() {
    this.readyState = 3 // CLOSED
    if (this.onclose) this.onclose({})
  }
}

// Mock fetch globally
global.fetch = jest.fn()

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: '',
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn(() => Promise.resolve()),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    }
  },
}))

// Mock environment variables
process.env.NODE_ENV = 'test'