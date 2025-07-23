# GET INN Frontend Implementation Specification (Updated)

## Overview

This document outlines the plan for enhancing the existing GET INN frontend application and implementing missing functionality. After a thorough review of the existing codebase, we've identified which components are already built and which still need implementation.

## Current Implementation Status

The current frontend implementation (frontend_v2) includes:

- Project setup with Vite, React 18, TypeScript, and Tailwind CSS
- shadcn/ui component library integration with a comprehensive set of components
- Complete application routing and layout structure
- Theme implementation (light/dark mode)
- All main pages have been implemented with basic functionality:
  - Dashboard
  - AI Supplier - Reconciliation
  - AI Supplier - Inventory
  - AI Labor - Onboarding
  - AI Chef - Menu
  - User Settings
  - Company Settings
- Mock API service with data structures for testing

## Implementation Priorities

Based on the analysis of the existing codebase, the following enhancements and missing features need to be implemented:

### 1. Authentication System

**Current Status:** Not implemented. There's no authentication context or login flow.

**Enhancement Requirements:**
- Implement AuthContext for user authentication state
- Create login and registration pages
- Add JWT token management
- Implement protected routes
- Add login persistence

**Implementation Details:**
```typescript
// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { mockApi } from '@/services/mockApi';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Check for existing auth in localStorage on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const storedUser = localStorage.getItem('user');
        
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }
      } catch (err) {
        // Invalid stored user
        localStorage.removeItem('user');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);
  
  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      
      // In a real implementation, this would be an API call
      // For now, using a mock login that just checks credentials
      if (email === 'admin@getinn.com' && password === 'password') {
        const userData = {
          id: 'user-001',
          name: 'Admin User',
          email: 'admin@getinn.com',
          role: 'admin'
        };
        
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        throw new Error('Invalid credentials');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const logout = async () => {
    localStorage.removeItem('user');
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      error, 
      login, 
      logout,
      isAuthenticated: !!user 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

**Login Page Implementation:**
```tsx
// src/pages/auth/Login.tsx
import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, error, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  
  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" />;
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      // Error is handled in AuthContext
    }
  };
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-muted/30">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-white rounded-lg p-2 flex items-center justify-center">
            <img 
              src="/lovable-uploads/48e2cdc5-2275-4a3a-bcae-5e8cf951bac5.png" 
              alt="GET INN Logo" 
              className="w-full h-full object-contain"
            />
          </div>
          <CardTitle className="text-2xl">Welcome to GET INN</CardTitle>
          <CardDescription>AI-Native Restaurant Operating System</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="#" className="text-sm text-primary hover:underline">
                  Forgot password?
                </a>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Logging in...' : 'Log In'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">
            Don't have an account?{' '}
            <a href="#" className="text-primary hover:underline">
              Contact your administrator
            </a>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Login;
```

**Protected Route Component:**
```tsx
// src/components/common/ProtectedRoute.tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-muted-foreground">Authenticating...</p>
      </div>
    </div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return <>{children}</>;
};
```

### 2. API Integration Layer

**Current Status:** Basic mock API exists, but no real API client implementation.

**Enhancement Requirements:**
- Create a proper API client
- Add error handling
- Add JWT auth token injection
- Implement real API endpoints according to specification

**Implementation Details:**
```typescript
// src/services/apiClient.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// For development, we'll still use the mock data but with a proper client structure
import { mockApi } from './mockApi';

class ApiError extends Error {
  public status: number;
  public data: any;
  
  constructor(message: string, status: number, data: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

export class ApiClient {
  private client: AxiosInstance;
  private useMock: boolean = true; // Toggle for using mock data vs real API
  
  constructor() {
    // Base URL would be replaced with real API base URL
    this.client = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors() {
    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const user = localStorage.getItem('user');
        if (user) {
          const { token } = JSON.parse(user);
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.message || 'An unexpected error occurred';
        const status = error.response?.status || 500;
        const data = error.response?.data || {};
        
        // Handle token expiration
        if (status === 401) {
          // Clear user data and redirect to login
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        
        return Promise.reject(new ApiError(message, status, data));
      }
    );
  }
  
  // Mock API request with simulated delay
  private async mockRequest<T>(method: string, endpoint: string, mockData: T): Promise<T> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 400));
    return mockData;
  }
  
  // Generic request method that handles both real and mock APIs
  private async request<T>(
    method: string, 
    endpoint: string, 
    mockData: T, 
    config?: AxiosRequestConfig,
    data?: any
  ): Promise<T> {
    if (this.useMock) {
      return this.mockRequest<T>(method, endpoint, mockData);
    }
    
    try {
      let response: AxiosResponse<T>;
      
      switch(method.toUpperCase()) {
        case 'GET':
          response = await this.client.get<T>(endpoint, config);
          break;
        case 'POST':
          response = await this.client.post<T>(endpoint, data, config);
          break;
        case 'PUT':
          response = await this.client.put<T>(endpoint, data, config);
          break;
        case 'DELETE':
          response = await this.client.delete<T>(endpoint, config);
          break;
        default:
          throw new Error(`Unsupported method: ${method}`);
      }
      
      return response.data;
    } catch (error) {
      // Re-throw ApiError or wrap other errors
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(
        (error as Error).message || 'Request failed',
        500,
        {}
      );
    }
  }
  
  // API methods using the mock API as fallback
  
  // Authentication
  async login(email: string, password: string) {
    return this.request<{token: string, user: any}>(
      'POST',
      '/auth/login',
      { token: 'mock-jwt-token', user: { id: 'user-001', name: 'Admin', email } },
      undefined,
      { email, password }
    );
  }
  
  // Restaurants
  async getRestaurants() {
    return this.request<any[]>(
      'GET',
      '/restaurants',
      await mockApi.getRestaurants()
    );
  }
  
  // Supplier - Reconciliation
  async getReconciliationStatus() {
    return this.request<any[]>(
      'GET',
      '/supplier/reconciliation/chain-status',
      await mockApi.getReconciliationStatus()
    );
  }
  
  async getReconciliationDocuments() {
    return this.request<any[]>(
      'GET',
      '/supplier/documents',
      await mockApi.getReconciliationDocuments()
    );
  }
  
  // Supplier - Inventory
  async getInventoryItems() {
    return this.request<any[]>(
      'GET',
      '/supplier/inventory/items',
      await mockApi.getInventoryItems()
    );
  }
  
  // Labor - Onboarding
  async getOnboardingStaff() {
    return this.request<any[]>(
      'GET',
      '/labor/onboarding/staff',
      await mockApi.getOnboardingStaff()
    );
  }
  
  // Chef - Menu
  async getMenuAnalysis() {
    return this.request<any[]>(
      'GET',
      '/chef/menu/abc-analysis',
      await mockApi.getMenuAnalysis()
    );
  }
}

// Create and export singleton instance
export const api = new ApiClient();
```

### 3. WebSocket Integration

**Current Status:** Not implemented. No WebSocket client or integration for real-time updates.

**Enhancement Requirements:**
- Create WebSocket service
- Add connection management
- Implement event handling for realtime updates
- Add reconnection logic

**Implementation Details:**
```typescript
// src/services/webSocketService.ts
import { useEffect, useRef, useState, useCallback } from 'react';

export class WebSocketService {
  private socket: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, Function[]> = new Map();
  private onConnectHandlers: Function[] = [];
  private onDisconnectHandlers: Function[] = [];
  
  constructor(url: string) {
    this.url = url;
  }
  
  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }
    
    try {
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.onConnectHandlers.forEach(handler => handler());
      };
      
      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message', error);
        }
      };
      
      this.socket.onclose = () => {
        this.onDisconnectHandlers.forEach(handler => handler());
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => this.reconnect(), this.reconnectDelay);
          this.reconnectAttempts++;
          this.reconnectDelay *= 2; // Exponential backoff
        } else {
          console.error('WebSocket connection failed after maximum attempts');
        }
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error', error);
      };
    } catch (error) {
      console.error('WebSocket connection error', error);
    }
  }
  
  private reconnect() {
    this.connect();
  }
  
  private handleMessage(data: any) {
    const { type, payload } = data;
    
    if (this.messageHandlers.has(type)) {
      const handlers = this.messageHandlers.get(type) || [];
      handlers.forEach(handler => handler(payload));
    }
  }
  
  subscribe(messageType: string, handler: Function) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    
    const handlers = this.messageHandlers.get(messageType) || [];
    handlers.push(handler);
    this.messageHandlers.set(messageType, handlers);
    
    return () => this.unsubscribe(messageType, handler);
  }
  
  unsubscribe(messageType: string, handler: Function) {
    if (this.messageHandlers.has(messageType)) {
      let handlers = this.messageHandlers.get(messageType) || [];
      handlers = handlers.filter(h => h !== handler);
      this.messageHandlers.set(messageType, handlers);
    }
  }
  
  onConnect(handler: Function) {
    this.onConnectHandlers.push(handler);
    return () => {
      this.onConnectHandlers = this.onConnectHandlers.filter(h => h !== handler);
    };
  }
  
  onDisconnect(handler: Function) {
    this.onDisconnectHandlers.push(handler);
    return () => {
      this.onDisconnectHandlers = this.onDisconnectHandlers.filter(h => h !== handler);
    };
  }
  
  send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error('WebSocket not connected');
    }
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

// React hook for WebSocket
export const useWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const serviceRef = useRef<WebSocketService | null>(null);
  
  useEffect(() => {
    const service = new WebSocketService(url);
    serviceRef.current = service;
    
    const onConnectCleanup = service.onConnect(() => setIsConnected(true));
    const onDisconnectCleanup = service.onDisconnect(() => setIsConnected(false));
    
    service.connect();
    
    return () => {
      onConnectCleanup();
      onDisconnectCleanup();
      service.disconnect();
    };
  }, [url]);
  
  const subscribe = useCallback((messageType: string, handler: Function) => {
    if (serviceRef.current) {
      return serviceRef.current.subscribe(messageType, handler);
    }
    return () => {};
  }, []);
  
  const send = useCallback((data: any) => {
    if (serviceRef.current) {
      serviceRef.current.send(data);
    }
  }, []);
  
  return { isConnected, subscribe, send };
};
```

### 4. Document Upload Functionality

**Current Status:** UI for document upload exists in Reconciliation page but without actual functionality.

**Enhancement Requirements:**
- Implement file upload with progress tracking
- Add drag and drop support
- Validate file types and size
- Handle upload errors

**Implementation Details:**
```tsx
// src/components/supplier/DocumentUpload.tsx
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/services/apiClient';

// Define allowed file types
const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
  'text/csv': ['.csv']
};

// 10MB max file size
const MAX_FILE_SIZE = 10 * 1024 * 1024;

interface DocumentUploadProps {
  onUploadComplete: () => void;
  restaurantId?: string; // Optional restaurant ID to associate with upload
}

interface FileWithProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'complete' | 'error';
  id?: string;
  errorMessage?: string;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ 
  onUploadComplete, 
  restaurantId 
}) => {
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    
    // Check file size
    const oversizedFiles = acceptedFiles.filter(file => file.size > MAX_FILE_SIZE);
    if (oversizedFiles.length > 0) {
      setError(`File(s) too large: ${oversizedFiles.map(f => f.name).join(', ')}. Maximum size is 10MB.`);
      return;
    }
    
    const newFiles = acceptedFiles.map(file => ({
      file,
      progress: 0,
      status: 'uploading' as const
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    
    // Start upload for each file
    newFiles.forEach(fileWithProgress => {
      uploadFile(fileWithProgress);
    });
  }, []);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE
  });
  
  const uploadFile = async (fileWithProgress: FileWithProgress) => {
    const formData = new FormData();
    formData.append('file', fileWithProgress.file);
    
    if (restaurantId) {
      formData.append('restaurantId', restaurantId);
    }
    
    try {
      // In a real implementation, we'd use the browser's fetch with progress monitoring
      // For this mock, we'll simulate progress updates
      const uploadInterval = setInterval(() => {
        setFiles(prev => prev.map(f => 
          f.file === fileWithProgress.file
            ? { ...f, progress: Math.min(f.progress + 10, 90) }
            : f
        ));
      }, 300);
      
      // Simulate API call with delay
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      clearInterval(uploadInterval);
      
      // Mock successful upload
      const mockResponse = {
        id: `doc-${Date.now()}`,
        filename: fileWithProgress.file.name
      };
      
      setFiles(prev => prev.map(f => 
        f.file === fileWithProgress.file
          ? { ...f, progress: 100, status: 'complete', id: mockResponse.id }
          : f
      ));
      
      // Trigger callback after successful upload
      onUploadComplete();
    } catch (err: any) {
      clearInterval(uploadInterval);
      
      setFiles(prev => prev.map(f => 
        f.file === fileWithProgress.file
          ? { ...f, status: 'error', errorMessage: err.message || 'Upload failed' }
          : f
      ));
    }
  };
  
  const removeFile = (fileToRemove: FileWithProgress) => {
    setFiles(prev => prev.filter(f => f.file !== fileToRemove.file));
  };
  
  return (
    <div className="space-y-4">
      {/* Dropzone area */}
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-lg p-8 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer ${
          isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">Upload Supplier Documents</h3>
        <p className="text-muted-foreground mb-4">
          {isDragActive 
            ? 'Drop the files here...' 
            : 'Drag and drop your supplier invoices here, or click to browse'
          }
        </p>
        <Button variant="outline">Choose Files</Button>
        <p className="text-xs text-muted-foreground mt-2">
          Supports PDF, Excel, CSV files up to 10MB
        </p>
      </div>
      
      {/* Error message */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {/* File list with progress */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Uploads</h4>
          {files.map((fileWithProgress, index) => (
            <div key={index} className="flex items-center space-x-4 border rounded-md p-3">
              <div className="flex-shrink-0">
                {fileWithProgress.status === 'complete' ? (
                  <CheckCircle className="h-6 w-6 text-green-500" />
                ) : fileWithProgress.status === 'error' ? (
                  <AlertCircle className="h-6 w-6 text-red-500" />
                ) : (
                  <FileText className="h-6 w-6 text-blue-500" />
                )}
              </div>
              
              <div className="flex-grow">
                <div className="flex justify-between items-center mb-1">
                  <div className="font-medium text-sm truncate" title={fileWithProgress.file.name}>
                    {fileWithProgress.file.name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {(fileWithProgress.file.size / 1024).toFixed(0)} KB
                  </div>
                </div>
                
                <Progress value={fileWithProgress.progress} className="h-1" />
                
                {fileWithProgress.errorMessage && (
                  <p className="text-xs text-red-500 mt-1">{fileWithProgress.errorMessage}</p>
                )}
              </div>
              
              <Button
                variant="ghost"
                size="icon"
                className="flex-shrink-0"
                onClick={() => removeFile(fileWithProgress)}
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Remove</span>
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
```

### 5. Real-time Updates Integration in Pages

**Current Status:** Pages are implemented but without real-time update functionality.

**Enhancement Requirements:**
- Add WebSocket connections to relevant pages
- Implement real-time data updates
- Add visual indicators for data changes
- Create notification system

**Implementation Details:**
```tsx
// src/components/common/WebSocketListener.tsx
import React, { useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useToast } from '@/components/ui/use-toast';
import { CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';

// This component handles global WebSocket connections and notifications
const WebSocketListener: React.FC = () => {
  const { toast } = useToast();
  const { subscribe, isConnected } = useWebSocket('wss://api.example.com/ws/chain/updates');
  
  // Handle status update notifications
  useEffect(() => {
    const handleStatusUpdate = (data: any) => {
      const { restaurantId, restaurantName, module, status, message } = data;
      
      let title = '';
      let description = message || '';
      let icon = null;
      let variant: 'default' | 'destructive' | undefined = undefined;
      
      // Determine notification appearance based on status
      switch (status) {
        case 'critical':
          title = `Critical Alert: ${restaurantName}`;
          variant = 'destructive';
          icon = <AlertCircle className="h-4 w-4" />;
          break;
        case 'warning':
          title = `Warning: ${restaurantName}`;
          icon = <AlertTriangle className="h-4 w-4 text-orange-500" />;
          break;
        case 'healthy':
          title = `Status Update: ${restaurantName}`;
          icon = <CheckCircle className="h-4 w-4 text-green-500" />;
          break;
        default:
          title = `${module} Update: ${restaurantName}`;
      }
      
      toast({
        title,
        description,
        variant,
        icon,
        duration: 5000
      });
    };
    
    if (isConnected) {
      // Subscribe to different event types
      const unsubStatusUpdate = subscribe('status_update', handleStatusUpdate);
      const unsubReconciliation = subscribe('reconciliation_update', handleStatusUpdate);
      const unsubInventory = subscribe('inventory_update', handleStatusUpdate);
      
      // Clean up subscriptions
      return () => {
        unsubStatusUpdate();
        unsubReconciliation();
        unsubInventory();
      };
    }
  }, [subscribe, toast, isConnected]);
  
  // This component doesn't render anything visual
  return null;
};

export default WebSocketListener;
```

**Integration in Reconciliation Page:**
```tsx
// Additions to src/pages/supplier/Reconciliation.tsx

// Add to imports
import { useWebSocket } from '@/hooks/useWebSocket';
import { Badge } from '@/components/ui/badge';

// Add inside the component
const Reconciliation = () => {
  // ...existing code
  
  const { subscribe, isConnected } = useWebSocket('wss://api.example.com/ws/supplier/reconciliation');
  const [liveUpdating, setLiveUpdating] = useState(false);
  
  // Real-time document updates
  useEffect(() => {
    if (isConnected) {
      setLiveUpdating(true);
      
      const unsubDocUpdate = subscribe('document_update', (data: any) => {
        // Update documents with new data
        setDocuments(prev => {
          const existingIndex = prev.findIndex(doc => doc.id === data.id);
          
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = data;
            return updated;
          } else {
            return [...prev, data];
          }
        });
      });
      
      const unsubStatusUpdate = subscribe('reconciliation_status_update', (data: any) => {
        // Update reconciliation status with new data
        setReconciliationStatus(prev => {
          const existingIndex = prev.findIndex(status => status.restaurantId === data.restaurantId);
          
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = data;
            return updated;
          } else {
            return [...prev, data];
          }
        });
      });
      
      return () => {
        unsubDocUpdate();
        unsubStatusUpdate();
        setLiveUpdating(false);
      };
    }
  }, [isConnected, subscribe]);
  
  // Add WebSocket status indicator in the UI
  // This would typically go in the header or tab area
  const connectionIndicator = (
    <Badge variant={isConnected ? "default" : "outline"} className="ml-2">
      {isConnected ? "Live" : "Offline"}
    </Badge>
  );
  
  // Add to JSX where appropriate
  // e.g. <CardTitle className="flex items-center gap-2">Chain-wide Reconciliation Status {connectionIndicator}</CardTitle>
};
```

### 6. Multi-language Support

**Current Status:** Translation context exists but without complete implementation.

**Enhancement Requirements:**
- Implement language switcher
- Add translation files
- Create hooks for easy translation usage
- Support multiple languages

**Implementation Details:**
```tsx
// src/contexts/TranslationContext.tsx (enhanced version)
import React, { createContext, useContext, useState, useEffect } from 'react';

// Define available languages
const LANGUAGES = {
  en: 'English',
  ru: 'Русский', // Russian
  es: 'Español'  // Spanish
};

// Translation structure
type Translations = {
  [key: string]: {
    [key: string]: string;
  };
};

// Initial translations (would be much more extensive in a real app)
const translations: Translations = {
  en: {
    'app.title': 'GET INN - AI Restaurant Platform',
    'dashboard.title': 'Dashboard',
    'dashboard.welcome': 'Welcome to GET INN - Your AI-Native Restaurant Operating System',
    'supplier.title': 'AI Supplier',
    'supplier.reconciliation': 'Reconciliation',
    'supplier.inventory': 'Inventory',
    'labor.title': 'AI Labor',
    'labor.onboarding': 'Onboarding',
    'chef.title': 'AI Chef',
    'chef.menu': 'Menu',
    'settings.title': 'Settings',
    'settings.user': 'User Settings',
    'settings.company': 'Company Settings',
    'settings.subscription': 'Subscription'
  },
  ru: {
    'app.title': 'GET INN - ИИ-платформа для ресторанов',
    'dashboard.title': 'Панель управления',
    'dashboard.welcome': 'Добро пожаловать в GET INN - Вашу ИИ-нативную операционную систему для ресторанов',
    'supplier.title': 'ИИ-поставщик',
    'supplier.reconciliation': 'Сверка',
    'supplier.inventory': 'Закупки',
    'labor.title': 'ИИ-персонал',
    'labor.onboarding': 'Адаптация',
    'chef.title': 'ИИ-шеф',
    'chef.menu': 'Меню',
    'settings.title': 'Настройки',
    'settings.user': 'Настройки пользователя',
    'settings.company': 'Настройки компании',
    'settings.subscription': 'Подписка'
  },
  es: {
    'app.title': 'GET INN - Plataforma de Restaurante IA',
    'dashboard.title': 'Tablero',
    'dashboard.welcome': 'Bienvenido a GET INN - Su sistema operativo de restaurante con tecnología de IA',
    'supplier.title': 'Proveedor IA',
    'supplier.reconciliation': 'Conciliación',
    'supplier.inventory': 'Inventario',
    'labor.title': 'Personal IA',
    'labor.onboarding': 'Incorporación',
    'chef.title': 'Chef IA',
    'chef.menu': 'Menú',
    'settings.title': 'Configuración',
    'settings.user': 'Configuración de usuario',
    'settings.company': 'Configuración de la empresa',
    'settings.subscription': 'Suscripción'
  }
};

interface TranslationContextType {
  language: string;
  setLanguage: (lang: string) => void;
  t: (key: string, params?: Record<string, string>) => string;
  availableLanguages: Record<string, string>;
}

const TranslationContext = createContext<TranslationContextType | undefined>(undefined);

export const TranslationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('language') || 'en';
    }
    return 'en';
  });
  
  useEffect(() => {
    localStorage.setItem('language', language);
    // Could also update HTML lang attribute
    document.documentElement.lang = language;
  }, [language]);
  
  const setLanguage = (lang: string) => {
    if (translations[lang]) {
      setLanguageState(lang);
    }
  };
  
  // Translation function with parameter support
  const t = (key: string, params?: Record<string, string>): string => {
    const translation = translations[language]?.[key] || translations.en[key] || key;
    
    if (!params) return translation;
    
    // Replace parameters in the format {{paramName}}
    return Object.entries(params).reduce(
      (text, [key, value]) => text.replace(new RegExp(`{{${key}}}`, 'g'), value),
      translation
    );
  };
  
  return (
    <TranslationContext.Provider value={{ 
      language, 
      setLanguage, 
      t,
      availableLanguages: LANGUAGES
    }}>
      {children}
    </TranslationContext.Provider>
  );
};

export const useTranslation = () => {
  const context = useContext(TranslationContext);
  if (context === undefined) {
    throw new Error('useTranslation must be used within a TranslationProvider');
  }
  return context;
};
```

**Language Selector Component:**
```tsx
// src/components/common/LanguageSelector.tsx
import React from 'react';
import { useTranslation } from '@/contexts/TranslationContext';
import { Button } from '@/components/ui/button';
import { 
  DropdownMenu, 
  DropdownMenuTrigger, 
  DropdownMenuContent, 
  DropdownMenuItem 
} from '@/components/ui/dropdown-menu';
import { Globe } from 'lucide-react';

const LanguageSelector: React.FC = () => {
  const { language, setLanguage, availableLanguages } = useTranslation();
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="flex items-center gap-2">
          <Globe className="h-4 w-4" />
          <span>{availableLanguages[language]}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {Object.entries(availableLanguages).map(([code, name]) => (
          <DropdownMenuItem 
            key={code}
            onClick={() => setLanguage(code)}
            className={language === code ? "bg-accent" : ""}
          >
            {name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default LanguageSelector;
```

## Development Roadmap

Based on the analysis of the current implementation and required enhancements, here's a prioritized roadmap:

### Phase 1: Authentication & API Integration

1. **Authentication System**
   - Implement AuthContext
   - Create login page
   - Add protected routes
   - Update App.tsx to wrap routes in protection

2. **API Integration Layer**
   - Create apiClient.ts
   - Refactor pages to use the API client
   - Add error handling
   - Support both mock and real API endpoints

### Phase 2: Realtime Functionality

1. **WebSocket Integration**
   - Implement WebSocket service
   - Create useWebSocket hook
   - Create WebSocketListener component
   - Add to App.tsx for global notifications

2. **Enhance Pages with Real-time Updates**
   - Update Reconciliation page
   - Update Dashboard
   - Add visual indicators for connection status

### Phase 3: User Experience Enhancements

1. **Document Upload Functionality**
   - Implement DocumentUpload component
   - Add to Reconciliation page
   - Support drag and drop

2. **Multi-language Support**
   - Enhance TranslationContext
   - Add translation files
   - Implement LanguageSelector
   - Update pages to use translations

3. **Polish & Optimization**
   - Add loading states for API calls
   - Implement skeleton loaders
   - Add error boundaries
   - Optimize performance

## Testing Guidelines

### Unit Testing

1. Component testing with React Testing Library or Vitest
   - Test component rendering and interactions
   - Test form validation
   - Test UI state changes

2. Hook testing
   - Test custom hooks like useAuth, useWebSocket
   - Test context providers

### Integration Testing

1. Test authentication flow
   - Login/logout process
   - Protected routes behavior

2. Test API client
   - Mock API responses
   - Test error handling

3. Test WebSocket functionality
   - Connection management
   - Message handling
   - Reconnection logic

### End-to-End Testing

1. Critical user flows
   - Login to dashboard
   - Document upload and reconciliation
   - Settings management

2. Cross-browser testing
   - Test on Chrome, Firefox, Safari
   - Test responsive design

## Design Guidelines

### Accessibility Improvements

1. **Semantic HTML**
   - Use proper heading hierarchy
   - Use semantic elements (article, section, etc.)

2. **ARIA attributes**
   - Add aria-labels to interactive elements
   - Use aria-live for dynamic content

3. **Keyboard Navigation**
   - Ensure all interactions are keyboard accessible
   - Add focus indicators

4. **Color Contrast**
   - Ensure sufficient contrast for text
   - Don't rely solely on color for information

### Performance Optimization

1. **Component Memoization**
   - Use React.memo for expensive components
   - Memoize callback functions

2. **Lazy Loading**
   - Implement code splitting for routes
   - Lazy load heavy components

3. **Data Handling**
   - Implement pagination for large datasets
   - Use virtualization for long lists
   - Cache data where appropriate

## Conclusion

The GET INN frontend application is already well-structured with most page implementations complete. The main enhancements needed are:

1. **Authentication system** for user management
2. **API integration layer** for connecting to backend services
3. **WebSocket functionality** for real-time updates
4. **Document upload** with progress tracking
5. **Multi-language support** enhancement

By implementing these features according to the roadmap, the application will provide a complete and robust user experience for managing AI-driven restaurant operations.