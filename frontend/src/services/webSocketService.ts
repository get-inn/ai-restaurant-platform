export class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3 seconds
  private listeners: Record<string, ((data: any) => void)[]> = {};
  private url: string;

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) return;

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log('WebSocket connection established');
        this.reconnectAttempts = 0;
        
        // Add auth token to connection if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          this.send('authenticate', { token });
        }
      };

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const { type, data } = message;
          
          if (this.listeners[type]) {
            this.listeners[type].forEach(callback => callback(data));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = () => {
        console.log('WebSocket connection closed');
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to establish WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  send(type: string, data: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, data }));
    } else {
      console.error('Cannot send message: WebSocket is not connected');
    }
  }

  on(type: string, callback: (data: any) => void) {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(callback);
  }

  off(type: string, callback?: (data: any) => void) {
    if (!callback) {
      delete this.listeners[type];
    } else if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter(cb => cb !== callback);
    }
  }
}

// Create WebSocket service (do not auto-connect - let components connect when needed)
export const ws = new WebSocketService(
  typeof window !== 'undefined' ?
    (window.location.protocol === 'https:' 
      ? `wss://${window.location.host}/ws` 
      : `ws://${window.location.host}/ws`) : ''
);