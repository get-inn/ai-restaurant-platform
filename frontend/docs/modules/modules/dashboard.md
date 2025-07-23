# Dashboard Module

The Dashboard module serves as the central hub of the GET INN platform, providing restaurant managers with a comprehensive overview of operations across multiple locations and key performance indicators.

## Overview

The Dashboard module delivers:

1. At-a-glance visibility into restaurant performance metrics
2. Real-time status indicators across all AI modules
3. Quick access to critical alerts and notifications
4. Customizable widget-based interface
5. Multi-location insights and comparisons

## Key Components

### Main Dashboard

The main dashboard interface includes:

- **Header**: Account selection, date range controls, and user menu
- **Status Cards**: High-level health indicators for each module
- **Metric Charts**: Key performance indicators visualized
- **Alert Panel**: Critical notifications requiring attention
- **Quick Action Buttons**: Shortcuts to common tasks

### Status Overview Section

This section provides health indicators for each core module:

- **AI Supplier Status**: Inventory health and reconciliation status
- **AI Labor Status**: Onboarding progress and staffing metrics
- **AI Chef Status**: Menu performance and recipe adherence

Each status card includes:
- Color-coded indicators (green/orange/red)
- Summary metric
- Change percentage from previous period
- Quick link to detailed view

### Performance Metrics Section

Displays key business metrics:

- **Sales Metrics**: Revenue, transaction count, average check
- **Cost Metrics**: Food cost percentage, labor cost percentage
- **Operational Metrics**: Inventory levels, staff efficiency
- **Trend Charts**: Visualizations of metric changes over time

## Dashboard Layout

```
┌───────────────────────────────────────────────────────────┐
│ Header: Account Selector, Date Range, User Menu           │
├───────────┬───────────┬───────────────────────────────────┤
│ Supplier  │ Labor     │ Recent                            │
│ Status    │ Status    │ Activity                          │
│           │           │                                   │
├───────────┼───────────┤                                   │
│ Chef      │ Operations│                                   │
│ Status    │ Status    │                                   │
│           │           │                                   │
├───────────┴───────────┼───────────────────────────────────┤
│ Sales & Revenue       │ Alerts &                          │
│ Metrics               │ Notifications                     │
│                       │                                   │
├───────────────────────┼───────────────────────────────────┤
│ Food Cost Trends      │ Quick                             │
│                       │ Actions                           │
│                       │                                   │
└───────────────────────┴───────────────────────────────────┘
```

## Implementation Details

### Data Structure

```typescript
interface DashboardData {
  timeRange: {
    start: Date;
    end: Date;
  };
  supplierStatus: {
    status: 'green' | 'orange' | 'red';
    reconciliationsPending: number;
    inventoryHealth: number;
    criticalItems: number;
  };
  laborStatus: {
    status: 'green' | 'orange' | 'red';
    onboardingInProgress: number;
    staffEfficiency: number;
    trainingCompletion: number;
  };
  chefStatus: {
    status: 'green' | 'orange' | 'red';
    menuPerformance: number;
    recipeAdherence: number;
    categoryAItems: number;
  };
  salesMetrics: {
    totalSales: number;
    comparedToLastPeriod: number;
    averageCheck: number;
    transactionCount: number;
  };
  costMetrics: {
    foodCostPercentage: number;
    laborCostPercentage: number;
    overallProfitMargin: number;
  };
  alerts: Alert[];
  recentActivity: Activity[];
}

interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  module: 'supplier' | 'labor' | 'chef' | 'operations';
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  link?: string;
}

interface Activity {
  id: string;
  type: string;
  module: 'supplier' | 'labor' | 'chef' | 'operations';
  description: string;
  user: string;
  timestamp: Date;
  link?: string;
}
```

### Main Components

The dashboard is built with these key components:

1. **DashboardLayout**: Main container with responsive grid layout
2. **StatusCard**: Reusable component for module status indicators
3. **MetricChart**: Visualization component for KPIs
4. **AlertList**: Interactive list of alerts with actions
5. **ActivityFeed**: Real-time activity log
6. **DateRangePicker**: Custom control for time period selection

### API Integration

The dashboard connects to multiple backend endpoints:

```typescript
// Fetch dashboard overview data
const fetchDashboardData = async (timeRange: TimeRange, locationIds?: string[]) => {
  const params = new URLSearchParams();
  params.append('start_date', timeRange.start.toISOString());
  params.append('end_date', timeRange.end.toISOString());
  
  if (locationIds && locationIds.length > 0) {
    locationIds.forEach(id => params.append('location_id', id));
  }
  
  const { data } = await api.get(`/v1/api/dashboard/overview?${params.toString()}`);
  return data;
};

// Fetch alerts
const fetchAlerts = async (acknowledged: boolean = false) => {
  const { data } = await api.get(`/v1/api/dashboard/alerts?acknowledged=${acknowledged}`);
  return data;
};

// Mark alert as acknowledged
const acknowledgeAlert = async (alertId: string) => {
  const { data } = await api.post(`/v1/api/dashboard/alerts/${alertId}/acknowledge`);
  return data;
};
```

## User Interactions

### Customizing the Dashboard

1. User clicks "Customize" button in dashboard header
2. Grid layout enters edit mode with draggable widgets
3. User can add, remove, resize, and reposition widgets
4. User clicks "Save Layout" to persist customizations
5. Dashboard reverts to normal view with new layout

### Filtering by Location

1. User selects locations from the account selector dropdown
2. Dashboard data automatically refreshes to show data for selected locations
3. User can select "All Locations" for aggregated view
4. User can compare locations by enabling comparison mode

### Responding to Alerts

1. User sees alert notification in the alerts panel
2. User clicks on alert to view details
3. User can:
   - Acknowledge the alert
   - Navigate to relevant section for resolution
   - Dismiss the alert
4. Alert status updates in real time

## Performance Optimizations

The Dashboard implements several optimizations:

1. **Partial Updates**: Only affected widgets update when data changes
2. **Data Caching**: React Query caches API responses to reduce calls
3. **Skeleton Loading**: Placeholder UI during data loading
4. **Lazy Loading**: Non-critical widgets load after initial render
5. **Data Aggregation**: Backend pre-aggregates data to reduce transfer size

## Customization Options

The Dashboard supports these customization features:

- **Widget Selection**: Choose which widgets to display
- **Layout Arrangement**: Position and size of widgets
- **Metric Selection**: Choose which metrics to highlight
- **Color Theme**: Light/dark mode and custom brand colors
- **Default View**: Save preferred dashboard configuration

## Integration with Other Modules

The Dashboard integrates with all other modules by:

1. Displaying summary data from each module
2. Providing quick links to detailed module views
3. Consolidating alerts from all modules
4. Tracking activity across all modules

## Technical Implementation Notes

- Uses React Grid Layout for drag-and-drop dashboard customization
- Implements websockets for real-time updates of critical metrics
- Uses Recharts for data visualization components
- Implements responsive design for all viewport sizes
- Uses React Query for efficient data fetching and caching