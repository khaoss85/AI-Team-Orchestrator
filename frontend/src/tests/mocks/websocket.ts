/**
 * WebSocket Mock for Testing Asset System Real-time Features
 * Provides comprehensive mocking for WebSocket connections in tests
 */

interface MockWebSocketMessage {
  type: string;
  [key: string]: any;
}

interface MockWebSocketOptions {
  url?: string;
  protocols?: string | string[];
}

class MockWebSocket {
  public static CONNECTING = 0;
  public static OPEN = 1;
  public static CLOSING = 2;
  public static CLOSED = 3;

  public readyState: number = MockWebSocket.CONNECTING;
  public url: string;
  public protocol: string = '';
  
  private listeners: { [event: string]: Function[] } = {};
  private messageQueue: MockWebSocketMessage[] = [];
  
  constructor(url: string, protocols?: string | string[]) {
    this.url = url;
    
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.dispatchEvent(new Event('open'));
    }, 10);
  }

  addEventListener(event: string, listener: Function): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(listener);
  }

  removeEventListener(event: string, listener: Function): void {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(l => l !== listener);
    }
  }

  dispatchEvent(event: Event): boolean {
    const eventListeners = this.listeners[event.type] || [];
    eventListeners.forEach(listener => listener(event));
    return true;
  }

  send(data: string): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    
    // Echo the message back for testing
    setTimeout(() => {
      const message = new MessageEvent('message', { data });
      this.dispatchEvent(message);
    }, 5);
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      this.dispatchEvent(new CloseEvent('close', { code: code || 1000, reason: reason || '' }));
    }, 5);
  }

  // Test helper methods
  simulateMessage(data: MockWebSocketMessage): void {
    if (this.readyState === MockWebSocket.OPEN) {
      const messageEvent = new MessageEvent('message', { 
        data: JSON.stringify(data) 
      });
      this.dispatchEvent(messageEvent);
    }
  }

  simulateError(error: string): void {
    const errorEvent = new ErrorEvent('error', { message: error });
    this.dispatchEvent(errorEvent);
  }

  simulateClose(code: number = 1000, reason: string = ''): void {
    this.readyState = MockWebSocket.CLOSED;
    const closeEvent = new CloseEvent('close', { code, reason });
    this.dispatchEvent(closeEvent);
  }
}

// Global WebSocket mock manager
class WebSocketMockManager {
  private originalWebSocket: typeof WebSocket;
  private mockInstances: MockWebSocket[] = [];
  private isSetup: boolean = false;

  setup(): void {
    if (this.isSetup) return;

    this.originalWebSocket = global.WebSocket;
    global.WebSocket = MockWebSocket as any;
    this.isSetup = true;
  }

  teardown(): void {
    if (!this.isSetup) return;

    global.WebSocket = this.originalWebSocket;
    this.mockInstances = [];
    this.isSetup = false;
  }

  getLastInstance(): MockWebSocket | undefined {
    return this.mockInstances[this.mockInstances.length - 1];
  }

  getAllInstances(): MockWebSocket[] {
    return [...this.mockInstances];
  }

  simulateMessage(data: MockWebSocketMessage, instanceIndex: number = -1): void {
    const instance = instanceIndex >= 0 
      ? this.mockInstances[instanceIndex]
      : this.getLastInstance();
    
    if (instance) {
      instance.simulateMessage(data);
    }
  }

  simulateError(error: string, instanceIndex: number = -1): void {
    const instance = instanceIndex >= 0 
      ? this.mockInstances[instanceIndex]
      : this.getLastInstance();
    
    if (instance) {
      instance.simulateError(error);
    }
  }

  simulateClose(code: number = 1000, reason: string = '', instanceIndex: number = -1): void {
    const instance = instanceIndex >= 0 
      ? this.mockInstances[instanceIndex]
      : this.getLastInstance();
    
    if (instance) {
      instance.simulateClose(code, reason);
    }
  }

  // Asset-specific message helpers
  simulateGoalProgressUpdate(data: {
    workspace_id: string;
    goal_id: string;
    progress: number;
    asset_completion_rate: number;
    quality_score: number;
  }): void {
    this.simulateMessage({
      type: 'goal_progress_update',
      ...data,
      timestamp: new Date().toISOString()
    });
  }

  simulateArtifactQualityUpdate(data: {
    workspace_id: string;
    artifact_id: string;
    quality_score: number;
    status: string;
    validation_feedback?: string;
  }): void {
    this.simulateMessage({
      type: 'artifact_quality_update',
      ...data,
      timestamp: new Date().toISOString()
    });
  }

  simulateNewArtifactCreated(data: {
    workspace_id: string;
    artifact: {
      id: string;
      artifact_name: string;
      artifact_type: string;
      status: string;
      quality_score: number;
    };
  }): void {
    this.simulateMessage({
      type: 'new_artifact_created',
      ...data,
      timestamp: new Date().toISOString()
    });
  }

  simulateQualityValidationComplete(data: {
    workspace_id: string;
    validation: {
      id: string;
      artifact_id: string;
      score: number;
      passed: boolean;
      feedback: string;
    };
  }): void {
    this.simulateMessage({
      type: 'quality_validation_complete',
      ...data,
      timestamp: new Date().toISOString()
    });
  }

  simulateHumanReviewRequested(data: {
    workspace_id: string;
    artifact: {
      id: string;
      artifact_name: string;
      artifact_type: string;
      quality_score: number;
      status: string;
    };
    review_reason: string;
  }): void {
    this.simulateMessage({
      type: 'human_review_requested',
      ...data,
      timestamp: new Date().toISOString()
    });
  }

  simulateAIEnhancementComplete(data: {
    workspace_id: string;
    artifact_id: string;
    enhanced_content: string;
    new_quality_score: number;
  }): void {
    this.simulateMessage({
      type: 'ai_enhancement_complete',
      ...data,
      timestamp: new Date().toISOString()
    });
  }
}

// Global instance
export const mockWebSocket = new WebSocketMockManager();

// Helper for React Testing Library
export const setupWebSocketMock = () => {
  beforeEach(() => {
    mockWebSocket.setup();
  });

  afterEach(() => {
    mockWebSocket.teardown();
  });
};

// Custom hooks for testing WebSocket components
export const useWebSocketTest = () => {
  return {
    simulateConnection: () => mockWebSocket.setup(),
    simulateDisconnection: () => mockWebSocket.simulateClose(),
    simulateMessage: (data: MockWebSocketMessage) => mockWebSocket.simulateMessage(data),
    simulateError: (error: string) => mockWebSocket.simulateError(error),
    getLastInstance: () => mockWebSocket.getLastInstance(),
    getAllInstances: () => mockWebSocket.getAllInstances()
  };
};

export default mockWebSocket;