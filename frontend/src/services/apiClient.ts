import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { mockApi } from './mockApi';

// Interfaces for API responses
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// Custom error class for API errors
export class ApiError extends Error {
  public status: number;
  public data: any;
  public isApiError: boolean = true;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export class ApiClient {
  private client: AxiosInstance;
  private useMock: boolean = true; // Toggle for using mock data vs real API
  private baseUrl: string = '';

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
    
    // Initialize Axios client
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 second timeout
    });
    
    // Set up request/response interceptors
    this.setupInterceptors();
  }

  /**
   * Configure whether to use mock data or real API
   * @param useMock - Whether to use mock data (true) or real API (false)
   */
  public setUseMock(useMock: boolean): void {
    this.useMock = useMock;
  }

  /**
   * Set up request and response interceptors for authentication and error handling
   */
  private setupInterceptors(): void {
    // Request interceptor for adding auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for handling errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const message = error.response?.data?.message || 'An unexpected error occurred';
        const status = error.response?.status || 500;
        const data = error.response?.data || {};
        
        // Handle token expiration (401 status)
        if (status === 401) {
          // Clear authentication data
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          
          // Redirect to login page if not already there
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }

        return Promise.reject(new ApiError(message, status, data));
      }
    );
  }

  /**
   * Generic request method that handles both real and mock APIs
   */
  private async request<T>(
    method: string,
    endpoint: string,
    mockDataProvider: () => Promise<T>,
    config?: AxiosRequestConfig,
    data?: any
  ): Promise<T> {
    // Use mock data if enabled
    if (this.useMock) {
      return await mockDataProvider();
    }

    try {
      let response;

      switch (method.toUpperCase()) {
        case 'GET':
          response = await this.client.get<ApiResponse<T>>(endpoint, config);
          break;
        case 'POST':
          response = await this.client.post<ApiResponse<T>>(endpoint, data, config);
          break;
        case 'PUT':
          response = await this.client.put<ApiResponse<T>>(endpoint, data, config);
          break;
        case 'PATCH':
          response = await this.client.patch<ApiResponse<T>>(endpoint, data, config);
          break;
        case 'DELETE':
          response = await this.client.delete<ApiResponse<T>>(endpoint, config);
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }

      return response.data.data;
    } catch (error) {
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

  // ========== Authentication API ==========

  /**
   * Login user
   * @param email - User email
   * @param password - User password
   * @returns User data and auth token
   */
  async login(email: string, password: string) {
    return this.request<{token: string; user: any}>(
      'POST',
      '/auth/login',
      async () => {
        // Mock login logic
        if (email && password) {
          await new Promise(resolve => setTimeout(resolve, 800)); // Simulate delay
          return {
            token: 'mock-jwt-token-' + Date.now(),
            user: { 
              id: 'user-001', 
              name: 'Иван Петров', 
              email, 
              role: 'manager' 
            }
          };
        }
        throw new ApiError('Invalid credentials', 401, { message: 'Invalid email or password' });
      },
      undefined,
      { email, password }
    );
  }

  /**
   * Logout user
   */
  async logout() {
    return this.request<{success: boolean}>(
      'POST',
      '/auth/logout',
      async () => {
        await new Promise(resolve => setTimeout(resolve, 300)); // Simulate delay
        return { success: true };
      }
    );
  }

  /**
   * Get current user information
   */
  async getCurrentUser() {
    return this.request<any>(
      'GET',
      '/auth/me',
      async () => {
        await new Promise(resolve => setTimeout(resolve, 300)); // Simulate delay
        const user = localStorage.getItem('user');
        if (!user) {
          throw new ApiError('Not authenticated', 401, { message: 'User is not authenticated' });
        }
        return JSON.parse(user);
      }
    );
  }

  /**
   * Refresh authentication token
   */
  async refreshToken() {
    return this.request<{token: string}>(
      'POST',
      '/auth/refresh',
      async () => {
        await new Promise(resolve => setTimeout(resolve, 300)); // Simulate delay
        return { token: 'mock-refreshed-jwt-token-' + Date.now() };
      }
    );
  }

  // ========== Restaurants API ==========

  /**
   * Get all restaurants
   */
  async getRestaurants() {
    return this.request(
      'GET',
      '/restaurants',
      async () => mockApi.getRestaurants()
    );
  }

  /**
   * Get restaurant by ID
   * @param id - Restaurant ID
   */
  async getRestaurantById(id: string) {
    return this.request(
      'GET',
      `/restaurants/${id}`,
      async () => {
        const restaurants = await mockApi.getRestaurants();
        const restaurant = restaurants.find(r => r.id === id);
        if (!restaurant) {
          throw new ApiError('Restaurant not found', 404, { message: 'Restaurant not found' });
        }
        return restaurant;
      }
    );
  }

  // ========== Supplier - Reconciliation API ==========

  /**
   * Get reconciliation status for all restaurants
   */
  async getReconciliationStatus() {
    return this.request(
      'GET',
      '/supplier/reconciliation/chain-status',
      async () => mockApi.getReconciliationStatus()
    );
  }

  /**
   * Get reconciliation documents
   * @param restaurantId - Optional restaurant ID for filtering
   */
  async getReconciliationDocuments(restaurantId?: string) {
    return this.request(
      'GET',
      `/supplier/documents${restaurantId ? `?restaurantId=${restaurantId}` : ''}`,
      async () => {
        const documents = await mockApi.getReconciliationDocuments();
        if (restaurantId) {
          return documents.filter(doc => doc.restaurantId === restaurantId);
        }
        return documents;
      }
    );
  }

  /**
   * Get specific reconciliation document
   * @param id - Document ID
   */
  async getReconciliationDocument(id: string) {
    return this.request(
      'GET',
      `/supplier/documents/${id}`,
      async () => {
        const documents = await mockApi.getReconciliationDocuments();
        const document = documents.find(doc => doc.id === id);
        if (!document) {
          throw new ApiError('Document not found', 404, { message: 'Document not found' });
        }
        return document;
      }
    );
  }

  /**
   * Upload reconciliation document
   * @param formData - Form data with document file
   * @param onProgress - Progress callback
   */
  async uploadReconciliationDocument(formData: FormData, onProgress?: (percent: number) => void) {
    const config: AxiosRequestConfig = {
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      }
    };

    return this.request(
      'POST',
      '/supplier/documents',
      async () => {
        // Simulate upload with progress
        let progress = 0;
        const interval = setInterval(() => {
          progress += 10;
          if (onProgress) {
            onProgress(Math.min(progress, 99));
          }
          if (progress >= 100) {
            clearInterval(interval);
          }
        }, 300);

        await new Promise(resolve => setTimeout(resolve, 3000)); // Simulate delay
        if (onProgress) {
          onProgress(100);
        }

        return {
          id: 'doc-' + Date.now(),
          filename: formData.get('file') ? (formData.get('file') as File).name : 'document.pdf',
          uploadDate: new Date().toISOString(),
          status: 'processing',
          restaurantId: formData.get('restaurantId')?.toString() || 'rest-001',
          restaurantName: 'Le Bernardin Manhattan',
          supplier: 'New Supplier',
          totalAmount: 0,
          itemCount: 0,
          currentStep: 1,
          steps: [
            { step: 1, title: 'Document Upload', status: 'completed', description: 'Document uploaded successfully', completedAt: new Date().toISOString() },
            { step: 2, title: 'Data Extraction', status: 'pending', description: 'Extracting data from document' },
            { step: 3, title: 'Restaurant Matching', status: 'pending', description: 'Matching with restaurant records' },
            { step: 4, title: 'Price Validation', status: 'pending', description: 'Validating pricing discrepancies' },
            { step: 5, title: 'Quantity Check', status: 'pending', description: 'Verifying quantities' },
            { step: 6, title: 'Exception Review', status: 'pending', description: 'Reviewing exceptions' },
            { step: 7, title: 'Manager Approval', status: 'pending', description: 'Awaiting approval' },
            { step: 8, title: 'System Integration', status: 'pending', description: 'Updating inventory systems' }
          ]
        };
      },
      config,
      formData
    );
  }

  /**
   * Start reconciliation process for a document
   * @param documentId - Document ID
   */
  async startReconciliation(documentId: string) {
    return this.request(
      'POST',
      `/supplier/reconciliation`,
      async () => {
        await new Promise(resolve => setTimeout(resolve, 800)); // Simulate delay
        return {
          id: 'recon-' + Date.now(),
          documentId,
          status: 'in-progress',
          startedAt: new Date().toISOString()
        };
      },
      undefined,
      { documentId }
    );
  }

  // ========== Supplier - Inventory API ==========

  /**
   * Get inventory items
   * @param restaurantId - Optional restaurant ID for filtering
   */
  async getInventoryItems(restaurantId?: string) {
    return this.request(
      'GET',
      `/supplier/inventory/items${restaurantId ? `?restaurantId=${restaurantId}` : ''}`,
      async () => {
        const items = await mockApi.getInventoryItems();
        if (restaurantId) {
          return items.filter(item => item.restaurantId === restaurantId);
        }
        return items;
      }
    );
  }

  /**
   * Get price changes for inventory items
   * @param restaurantId - Optional restaurant ID for filtering
   */
  async getInventoryPriceChanges(restaurantId?: string) {
    return this.request(
      'GET',
      `/supplier/inventory/price-changes${restaurantId ? `?restaurantId=${restaurantId}` : ''}`,
      async () => {
        const items = await mockApi.getInventoryItems();
        const filtered = restaurantId ? 
          items.filter(item => item.restaurantId === restaurantId) : 
          items;
        
        return filtered.map(item => ({
          id: item.id,
          name: item.name,
          previous_price: item.price / (1 + item.priceChange / 100),
          current_price: item.price,
          change_percentage: item.priceChange,
          restaurantId: item.restaurantId
        }));
      }
    );
  }

  // ========== Labor - Onboarding API ==========

  /**
   * Get onboarding staff
   * @param restaurantId - Optional restaurant ID for filtering
   */
  async getOnboardingStaff(restaurantId?: string) {
    return this.request(
      'GET',
      `/labor/onboarding/staff${restaurantId ? `?restaurantId=${restaurantId}` : ''}`,
      async () => {
        const staff = await mockApi.getOnboardingStaff();
        if (restaurantId) {
          return staff.filter(person => person.restaurantId === restaurantId);
        }
        return staff;
      }
    );
  }

  /**
   * Get onboarding details for specific staff member
   * @param id - Staff ID
   */
  async getOnboardingDetails(id: string) {
    return this.request(
      'GET',
      `/labor/onboarding/${id}`,
      async () => {
        const allStaff = await mockApi.getOnboardingStaff();
        const staff = allStaff.find(person => person.id === id);
        
        if (!staff) {
          throw new ApiError('Staff member not found', 404, { message: 'Staff member not found' });
        }
        
        // Add additional onboarding details that aren't in the basic staff list
        return {
          ...staff,
          trainingModules: [
            {
              id: 'module-1',
              name: 'Company Introduction',
              status: 'completed',
              completedAt: '2024-12-20T10:00:00Z',
              score: 95
            },
            {
              id: 'module-2',
              name: 'Food Safety',
              status: staff.currentProgress >= 50 ? 'completed' : 'in-progress',
              completedAt: staff.currentProgress >= 50 ? '2024-12-25T15:30:00Z' : undefined,
              score: staff.currentProgress >= 50 ? 87 : undefined
            },
            {
              id: 'module-3',
              name: 'Customer Service',
              status: staff.currentProgress >= 75 ? 'completed' : 'pending',
              completedAt: staff.currentProgress >= 75 ? '2024-12-28T11:15:00Z' : undefined,
              score: staff.currentProgress >= 75 ? 92 : undefined
            },
            {
              id: 'module-4',
              name: 'Kitchen Operations',
              status: staff.currentProgress >= 100 ? 'completed' : 'pending',
              completedAt: staff.currentProgress >= 100 ? '2025-01-05T14:20:00Z' : undefined,
              score: staff.currentProgress >= 100 ? 89 : undefined
            }
          ]
        };
      }
    );
  }

  // ========== Chef - Menu API ==========

  /**
   * Get menu ABC analysis
   * @param restaurantId - Optional restaurant ID for filtering
   */
  async getMenuAnalysis(restaurantId?: string) {
    return this.request(
      'GET',
      `/chef/menu/abc-analysis${restaurantId ? `?restaurantId=${restaurantId}` : ''}`,
      async () => {
        const menuItems = await mockApi.getMenuAnalysis();
        if (restaurantId) {
          return menuItems.filter(item => item.restaurantId === restaurantId);
        }
        return menuItems;
      }
    );
  }

  /**
   * Get menu item performance details
   * @param id - Menu item ID
   */
  async getMenuItemPerformance(id: string) {
    return this.request(
      'GET',
      `/chef/menu/item/${id}/performance`,
      async () => {
        const menuItems = await mockApi.getMenuAnalysis();
        const item = menuItems.find(menuItem => menuItem.id === id);
        
        if (!item) {
          throw new ApiError('Menu item not found', 404, { message: 'Menu item not found' });
        }
        
        // Add performance metrics that aren't in the basic menu item
        return {
          ...item,
          weeklyTrend: [
            { date: '2024-01-01', sales: item.salesCount * 0.8 },
            { date: '2024-01-08', sales: item.salesCount * 0.85 },
            { date: '2024-01-15', sales: item.salesCount * 0.95 },
            { date: '2024-01-22', sales: item.salesCount * 1.0 },
            { date: '2024-01-29', sales: item.salesCount * 1.1 }
          ],
          ingredients: [
            { name: 'Primary Ingredient', cost: item.revenue * (1 - item.profitMargin / 100) * 0.5 },
            { name: 'Secondary Ingredient', cost: item.revenue * (1 - item.profitMargin / 100) * 0.3 },
            { name: 'Other Ingredients', cost: item.revenue * (1 - item.profitMargin / 100) * 0.2 }
          ],
          comparableDishes: menuItems
            .filter(otherItem => otherItem.id !== id && otherItem.category === item.category)
            .slice(0, 3)
        };
      }
    );
  }

  /**
   * Get AI-generated menu insights
   * @param restaurantId - Optional restaurant ID for filtering
   */
  async getMenuInsights(restaurantId?: string) {
    return this.request(
      'GET',
      `/chef/menu/insights${restaurantId ? `?restaurantId=${restaurantId}` : ''}`,
      async () => {
        await new Promise(resolve => setTimeout(resolve, 800)); // Simulate delay
        
        // Generate some generic insights
        return [
          {
            id: 'insight-1',
            type: 'opportunity',
            title: 'Seafood Menu Opportunity',
            description: 'Your seafood dishes consistently outperform other categories with 15% higher profit margins.',
            recommendation: 'Consider expanding your seafood offerings with 2-3 new dishes highlighting seasonal catches.'
          },
          {
            id: 'insight-2',
            type: 'risk',
            title: 'Dessert Performance Declining',
            description: 'Dessert sales have declined 12% over the past month, particularly on weekdays.',
            recommendation: 'Review dessert pricing and consider weekday promotions to boost attachment rate.'
          },
          {
            id: 'insight-3',
            type: 'efficiency',
            title: 'Menu Simplification',
            description: '5 dishes in your "C" category have high ingredient overlap but low sales.',
            recommendation: 'Consider consolidating these items to reduce inventory complexity while maintaining variety.'
          }
        ];
      }
    );
  }

  // ========== Settings API ==========

  /**
   * Update user settings
   * @param settings - User settings to update
   */
  async updateUserSettings(settings: any) {
    return this.request(
      'PUT',
      '/settings/user',
      async () => {
        await new Promise(resolve => setTimeout(resolve, 600)); // Simulate delay
        return {
          success: true,
          message: 'User settings updated successfully'
        };
      },
      undefined,
      settings
    );
  }

  /**
   * Update company settings
   * @param settings - Company settings to update
   */
  async updateCompanySettings(settings: any) {
    return this.request(
      'PUT',
      '/settings/company',
      async () => {
        await new Promise(resolve => setTimeout(resolve, 600)); // Simulate delay
        return {
          success: true,
          message: 'Company settings updated successfully'
        };
      },
      undefined,
      settings
    );
  }
}

// Create and export a singleton instance
export const api = new ApiClient();