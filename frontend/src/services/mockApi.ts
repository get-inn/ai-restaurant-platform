export interface Restaurant {
  id: string;
  name: string;
  location: string;
  manager: string;
  status: 'healthy' | 'warning' | 'critical';
}

export interface WasteReason {
  id: string;
  name: string;
  allowedPercentage: number;
}

export interface DateRange {
  startDate: Date;
  endDate: Date;
}

export interface HistoricalQuantity {
  date: string; // ISO string
  quantity: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  category: string;
  currentStock: number;
  recommendedLevel: number;
  unit: string;
  price: number;
  priceChange: number;
  status: 'healthy' | 'warning' | 'critical';
  restaurantId: string;
  dishUsageCount: number;
  salesPercentage: number;
  wasteQuantity?: number;
  wastePercentage?: number;
  wasteReasonId?: string;
  historicalData?: HistoricalQuantity[];
}

export interface ReconciliationStatus {
  restaurantId: string;
  restaurantName: string;
  totalItems: number;
  matchedItems: number;
  discrepancies: number;
  status: 'healthy' | 'warning' | 'critical';
  lastUpdate: string;
}

export interface ReconciliationDocument {
  id: string;
  filename: string;
  uploadDate: string;
  status: 'processing' | 'completed' | 'error';
  restaurantId: string;
  restaurantName: string;
  supplier: string;
  totalAmount: number;
  itemCount: number;
  currentStep: number;
  steps: ReconciliationStep[];
}

export interface ReconciliationStep {
  step: number;
  title: string;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  description: string;
  completedAt?: string;
}

export interface OnboardingStaff {
  id: string;
  name: string;
  restaurantId: string;
  restaurantName: string;
  position: string;
  startDate: string;
  plannedExamDate: string;
  currentProgress: number;
  status: 'not-started' | 'in-progress' | 'completed';
  avatar?: string;
}

export interface MenuAnalysisItem {
  id: string;
  name: string;
  category: 'A' | 'B' | 'C';
  revenue: number;
  profitMargin: number;
  popularityScore: number;
  salesCount: number;
  restaurantId: string;
  restaurantName: string;
}

export interface InventorySettings {
  wasteReasons: WasteReason[];
}

const mockApi = {
  getRestaurants: async (): Promise<Restaurant[]> => {
    await new Promise(resolve => setTimeout(resolve, 400));
    
    return [
      {
        id: 'rest-001',
        name: 'Чихо Манхэттен',
        location: 'New York, NY',
        manager: 'Лю Вэй',
        status: 'healthy'
      },
      {
        id: 'rest-002',
        name: 'Чихо Беверли Хиллз',
        location: 'Beverly Hills, CA',
        manager: 'Чжан Мин',
        status: 'warning'
      },
      {
        id: 'rest-003',
        name: 'Чихо Майами',
        location: 'Miami, FL',
        manager: 'Ван Цзин',
        status: 'critical'
      }
    ];
  },

  getInventoryItems: async (dateRange?: DateRange): Promise<InventoryItem[]> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    // If date range is provided, log it for debugging
    if (dateRange) {
      console.log(`Fetching inventory data for date range: ${dateRange.startDate.toISOString()} - ${dateRange.endDate.toISOString()}`);
    }
    
    return [
      {
        id: 'inv-001',
        name: 'Рисовая лапша',
        category: 'Злаки',
        currentStock: 45,
        recommendedLevel: 60,
        unit: 'кг',
        price: 18.50,
        priceChange: 5.2,
        status: 'warning',
        restaurantId: 'rest-001',
        dishUsageCount: 8,
        salesPercentage: 15.3,
        wasteQuantity: 1.8, // in kg (unit)  
        wastePercentage: 3.0, // of total (currentStock + wasteQuantity)
        wasteReasonId: 'waste-001', // Spoilage
        historicalData: [
          { date: '2025-07-01', quantity: 50 },
          { date: '2025-07-03', quantity: 48 },
          { date: '2025-07-05', quantity: 46 },
          { date: '2025-07-08', quantity: 45 },
          { date: '2025-07-10', quantity: 43 },
          { date: '2025-07-12', quantity: 45 }
        ]
      },
      {
        id: 'inv-002',
        name: 'Тофу',
        category: 'Белки',
        currentStock: 12,
        recommendedLevel: 25,
        unit: 'блоков',
        price: 32.00,
        priceChange: -2.1,
        status: 'critical',
        restaurantId: 'rest-001',
        dishUsageCount: 4,
        salesPercentage: 22.7,
        wasteQuantity: 0.5, 
        wastePercentage: 4.0, 
        wasteReasonId: 'waste-002', // Preparation Error
        historicalData: [
          { date: '2025-07-01', quantity: 18 },
          { date: '2025-07-03', quantity: 16 },
          { date: '2025-07-05', quantity: 15 },
          { date: '2025-07-08', quantity: 14 },
          { date: '2025-07-10', quantity: 12 },
          { date: '2025-07-12', quantity: 12 }
        ]
      },
      {
        id: 'inv-003',
        name: 'Пак-чой',
        category: 'Овощи',
        currentStock: 80,
        recommendedLevel: 50,
        unit: 'кг',
        price: 4.25,
        priceChange: 1.8,
        status: 'healthy',
        restaurantId: 'rest-002',
        dishUsageCount: 12,
        salesPercentage: 8.4,
        wasteQuantity: 1.2,
        wastePercentage: 1.5,
        wasteReasonId: 'waste-001', // Spoilage
        historicalData: [
          { date: '2025-07-01', quantity: 72 },
          { date: '2025-07-03', quantity: 75 },
          { date: '2025-07-05', quantity: 78 },
          { date: '2025-07-08', quantity: 82 },
          { date: '2025-07-10', quantity: 80 },
          { date: '2025-07-12', quantity: 80 }
        ]
      },
      {
        id: 'inv-004',
        name: 'Соевый соус',
        category: 'Соусы',
        currentStock: 15,
        recommendedLevel: 30,
        unit: 'бутылок',
        price: 28.75,
        priceChange: 8.9,
        status: 'warning',
        restaurantId: 'rest-002',
        dishUsageCount: 6,
        salesPercentage: 18.9,
        wasteQuantity: 2,
        wastePercentage: 11.8,
        wasteReasonId: 'waste-005', // Inventory Damage
        historicalData: [
          { date: '2025-07-01', quantity: 20 },
          { date: '2025-07-03', quantity: 19 },
          { date: '2025-07-05', quantity: 18 },
          { date: '2025-07-08', quantity: 17 },
          { date: '2025-07-10', quantity: 16 },
          { date: '2025-07-12', quantity: 15 }
        ]
      },
      {
        id: 'inv-005',
        name: 'Имбирь',
        category: 'Специи',
        currentStock: 8,
        recommendedLevel: 20,
        unit: 'кг',
        price: 24.50,
        priceChange: -1.5,
        status: 'critical',
        restaurantId: 'rest-003',
        dishUsageCount: 5,
        salesPercentage: 12.6,
        wasteQuantity: 0.2,
        wastePercentage: 2.4,
        wasteReasonId: 'waste-003', // Overproduction
        historicalData: [
          { date: '2025-07-01', quantity: 10 },
          { date: '2025-07-03', quantity: 9 },
          { date: '2025-07-05', quantity: 9 },
          { date: '2025-07-08', quantity: 8 },
          { date: '2025-07-10', quantity: 8 },
          { date: '2025-07-12', quantity: 8 }
        ]
      },
      {
        id: 'inv-006',
        name: 'Кунжутное масло',
        category: 'Масла',
        currentStock: 35,
        recommendedLevel: 25,
        unit: 'бутылок',
        price: 45.00,
        priceChange: 3.2,
        status: 'healthy',
        restaurantId: 'rest-003',
        dishUsageCount: 15,
        salesPercentage: 6.8,
        wasteQuantity: 0,
        wastePercentage: 0,
        wasteReasonId: null,
        historicalData: [
          { date: '2025-07-01', quantity: 30 },
          { date: '2025-07-03', quantity: 32 },
          { date: '2025-07-05', quantity: 33 },
          { date: '2025-07-08', quantity: 34 },
          { date: '2025-07-10', quantity: 35 },
          { date: '2025-07-12', quantity: 35 }
        ]
      }
    ];
    
    if (dateRange) {
      // Process each item to adjust quantities based on date range
      const processedItems = items.map(item => {
        if (!item.historicalData) return item;
        
        // Find the closest date to the endDate in the range
        const relevantData = item.historicalData
          .filter(hd => {
            const date = new Date(hd.date);
            return date >= dateRange.startDate && date <= dateRange.endDate;
          })
          .sort((a, b) => {
            // Sort to find the closest date to the endDate
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return Math.abs(dateB.getTime() - dateRange.endDate.getTime()) - 
                   Math.abs(dateA.getTime() - dateRange.endDate.getTime());
          });
          
        // Use the most relevant data point, or current if none found
        if (relevantData.length > 0) {
          const latestQuantity = relevantData[0].quantity;
          // Calculate a new waste percentage based on the historical quantity
          const adjustedWastePercentage = item.wasteQuantity ? 
            (item.wasteQuantity / (latestQuantity + item.wasteQuantity)) * 100 : 0;
            
          return {
            ...item,
            currentStock: latestQuantity,
            wastePercentage: Math.round(adjustedWastePercentage * 10) / 10
          };
        }
        
        return item;
      });
      
      return processedItems;
    }
    
    return items;
  },

  getReconciliationStatus: async (): Promise<ReconciliationStatus[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));

    return [
      {
        restaurantId: 'rest-001',
        restaurantName: 'Чихо Манхэттен',
        totalItems: 125,
        matchedItems: 118,
        discrepancies: 2,
        status: 'healthy',
        lastUpdate: '2024-12-29T14:30:00Z'
      },
      {
        restaurantId: 'rest-002',
        restaurantName: 'Чихо Беверли Хиллз',
        totalItems: 95,
        matchedItems: 89,
        discrepancies: 4,
        status: 'warning',
        lastUpdate: '2024-12-29T13:45:00Z'
      },
      {
        restaurantId: 'rest-003',
        restaurantName: 'Чихо Майами',
        totalItems: 75,
        matchedItems: 62,
        discrepancies: 8,
        status: 'critical',
        lastUpdate: '2024-12-29T12:00:00Z'
      }
    ];
  },

  getReconciliationDocuments: async (): Promise<ReconciliationDocument[]> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    return [
      {
        id: 'doc-001',
        filename: 'sysco_invoice_2024_001.pdf',
        uploadDate: '2024-12-28T10:30:00Z',
        status: 'completed',
        restaurantId: 'rest-001',
        restaurantName: 'Чихо Манхэттен',
        supplier: 'Sysco Foods',
        totalAmount: 8750.50,
        itemCount: 45,
        currentStep: 8,
        steps: [
          { step: 1, title: 'Document Upload', status: 'completed', description: 'Supplier invoice uploaded', completedAt: '2024-12-28T10:30:00Z' },
          { step: 2, title: 'Data Extraction', status: 'completed', description: 'AI extracted line items', completedAt: '2024-12-28T10:32:00Z' },
          { step: 3, title: 'Restaurant Matching', status: 'completed', description: 'Matched with restaurant records', completedAt: '2024-12-28T10:35:00Z' },
          { step: 4, title: 'Price Validation', status: 'completed', description: 'Validated pricing discrepancies', completedAt: '2024-12-28T10:38:00Z' },
          { step: 5, title: 'Quantity Check', status: 'completed', description: 'Verified delivered quantities', completedAt: '2024-12-28T10:42:00Z' },
          { step: 6, title: 'Exception Review', status: 'completed', description: 'Reviewed flagged items', completedAt: '2024-12-28T10:45:00Z' },
          { step: 7, title: 'Manager Approval', status: 'completed', description: 'Final approval completed', completedAt: '2024-12-28T11:00:00Z' },
          { step: 8, title: 'System Integration', status: 'completed', description: 'Updated inventory systems', completedAt: '2024-12-28T11:05:00Z' }
        ]
      },
      {
        id: 'doc-002',
        filename: 'fresh_direct_invoice_2024_045.pdf',
        uploadDate: '2024-12-29T14:15:00Z',
        status: 'processing',
        restaurantId: 'rest-002',
        restaurantName: 'Чихо Беверли Хиллз',
        supplier: 'Fresh Direct',
        totalAmount: 5430.25,
        itemCount: 32,
        currentStep: 3,
        steps: [
          { step: 1, title: 'Document Upload', status: 'completed', description: 'Supplier invoice uploaded', completedAt: '2024-12-29T14:15:00Z' },
          { step: 2, title: 'Data Extraction', status: 'completed', description: 'AI extracted line items', completedAt: '2024-12-29T14:17:00Z' },
          { step: 3, title: 'Restaurant Matching', status: 'in-progress', description: 'Matching with restaurant records' },
          { step: 4, title: 'Price Validation', status: 'pending', description: 'Validate pricing discrepancies' },
          { step: 5, title: 'Quantity Check', status: 'pending', description: 'Verify delivered quantities' },
          { step: 6, title: 'Exception Review', status: 'pending', description: 'Review flagged items' },
          { step: 7, title: 'Manager Approval', status: 'pending', description: 'Final approval required' },
          { step: 8, title: 'System Integration', status: 'pending', description: 'Update inventory systems' }
        ]
      },
      {
        id: 'doc-003',
        filename: 'us_foods_invoice_2024_198.pdf',
        uploadDate: '2024-12-29T16:45:00Z',
        status: 'error',
        restaurantId: 'rest-003',
        restaurantName: 'Чихо Майами',
        supplier: 'US Foods',
        totalAmount: 12890.75,
        itemCount: 67,
        currentStep: 2,
        steps: [
          { step: 1, title: 'Document Upload', status: 'completed', description: 'Supplier invoice uploaded', completedAt: '2024-12-29T16:45:00Z' },
          { step: 2, title: 'Data Extraction', status: 'error', description: 'Error extracting line items - document format not recognized' },
          { step: 3, title: 'Restaurant Matching', status: 'pending', description: 'Matching with restaurant records' },
          { step: 4, title: 'Price Validation', status: 'pending', description: 'Validate pricing discrepancies' },
          { step: 5, title: 'Quantity Check', status: 'pending', description: 'Verify delivered quantities' },
          { step: 6, title: 'Exception Review', status: 'pending', description: 'Review flagged items' },
          { step: 7, title: 'Manager Approval', status: 'pending', description: 'Final approval required' },
          { step: 8, title: 'System Integration', status: 'pending', description: 'Update inventory systems' }
        ]
      }
    ];
  },

  getOnboardingStaff: async (): Promise<OnboardingStaff[]> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return [
      {
        id: 'staff-001',
        name: 'Мария Иванова',
        restaurantId: 'rest-001',
        restaurantName: 'Чихо Манхэттен',
        position: 'Су-шеф',
        startDate: '2024-12-15',
        plannedExamDate: '2025-01-15',
        currentProgress: 75,
        status: 'in-progress'
      },
      {
        id: 'staff-002',
        name: 'Александр Петров',
        restaurantId: 'rest-001',
        restaurantName: 'Чихо Манхэттен',
        position: 'Повар',
        startDate: '2024-12-20',
        plannedExamDate: '2025-01-20',
        currentProgress: 45,
        status: 'in-progress'
      },
      {
        id: 'staff-003',
        name: 'Екатерина Смирнова',
        restaurantId: 'rest-002',
        restaurantName: 'Чихо Беверли Хиллз',
        position: 'Кондитер',
        startDate: '2024-12-10',
        plannedExamDate: '2025-01-10',
        currentProgress: 100,
        status: 'completed'
      },
      {
        id: 'staff-004',
        name: 'Дмитрий Соколов',
        restaurantId: 'rest-002',
        restaurantName: 'Чихо Беверли Хиллз',
        position: 'Официант',
        startDate: '2025-01-02',
        plannedExamDate: '2025-02-02',
        currentProgress: 15,
        status: 'in-progress'
      },
      {
        id: 'staff-005',
        name: 'Анна Козлова',
        restaurantId: 'rest-003',
        restaurantName: 'Чихо Майами',
        position: 'Сомелье',
        startDate: '2025-01-05',
        plannedExamDate: '2025-02-05',
        currentProgress: 0,
        status: 'not-started'
      }
    ];
  },

  getWasteReasons: async (): Promise<WasteReason[]> => {
    await new Promise(resolve => setTimeout(resolve, 300));

    return [
      {
        id: 'waste-001',
        name: 'Порча',
        allowedPercentage: 2.0
      },
      {
        id: 'waste-002',
        name: 'Ошибка приготовления',
        allowedPercentage: 1.5
      },
      {
        id: 'waste-003',
        name: 'Перепроизводство',
        allowedPercentage: 3.0
      },
      {
        id: 'waste-004',
        name: 'Возврат клиентом',
        allowedPercentage: 0.5
      },
      {
        id: 'waste-005',
        name: 'Повреждение при хранении',
        allowedPercentage: 1.0
      }
    ];
  },

  updateWasteReasonAllowance: async (id: string, percentage: number): Promise<WasteReason> => {
    // This would typically update a database, but for our mock just return a success response
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return {
      id,
      name: id === 'waste-001' ? 'Порча' :
            id === 'waste-002' ? 'Ошибка приготовления' :
            id === 'waste-003' ? 'Перепроизводство' :
            id === 'waste-004' ? 'Возврат клиентом' : 'Повреждение при хранении',
      allowedPercentage: percentage
    };
  },
  
  getMenuAnalysis: async (dateRange?: DateRange): Promise<MenuAnalysisItem[]> => {
    await new Promise(resolve => setTimeout(resolve, 700));
    
    return [
      {
        id: 'menu-001',
        name: 'Утка по-пекински',
        category: 'A',
        revenue: 15840,
        profitMargin: 68,
        popularityScore: 92,
        salesCount: 264,
        restaurantId: 'rest-001',
        restaurantName: 'Чихо Манхэттен'
      },
      {
        id: 'menu-002',
        name: 'Димсам ассорти',
        category: 'A',
        revenue: 22350,
        profitMargin: 72,
        popularityScore: 85,
        salesCount: 149,
        restaurantId: 'rest-001',
        restaurantName: 'Чихо Манхэттен'
      },
      {
        id: 'menu-003',
        name: 'Кунг Пао с курицей',
        category: 'B',
        revenue: 8920,
        profitMargin: 58,
        popularityScore: 67,
        salesCount: 178,
        restaurantId: 'rest-002',
        restaurantName: 'Чихо Беверли Хиллз'
      },
      {
        id: 'menu-004',
        name: 'Жареный рис с овощами',
        category: 'B',
        revenue: 6840,
        profitMargin: 62,
        popularityScore: 71,
        salesCount: 114,
        restaurantId: 'rest-002',
        restaurantName: 'Чихо Беверли Хиллз'
      },
      {
        id: 'menu-005',
        name: 'Лапша с говядиной',
        category: 'C',
        revenue: 3450,
        profitMargin: 45,
        popularityScore: 42,
        salesCount: 69,
        restaurantId: 'rest-003',
        restaurantName: 'Чихо Майами'
      },
      {
        id: 'menu-006',
        name: 'Баклажаны в кисло-сладком соусе',
        category: 'C',
        revenue: 4120,
        profitMargin: 38,
        popularityScore: 51,
        salesCount: 82,
        restaurantId: 'rest-003',
        restaurantName: 'Чихо Майами'
      }
    ];
  }
};

export { mockApi };
