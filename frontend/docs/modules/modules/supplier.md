# AI Supplier Module

The AI Supplier module provides intelligent procurement and inventory management capabilities for restaurant operations, focusing on reconciliation and inventory tracking.

## Overview

The AI Supplier module consists of two primary components:

1. **Reconciliation**: Automated invoice reconciliation and financial document management
2. **Inventory**: Real-time inventory tracking and analytics

## Reconciliation

The reconciliation interface enables restaurant managers to upload, process, and reconcile supplier invoices with internal systems.

### Features

- **Document Upload**: Drag-and-drop interface for uploading supplier documents
- **Multi-step Reconciliation Process**: 8-step automated reconciliation workflow
- **Real-time Processing**: WebSocket integration for live progress updates
- **Results Analysis**: Identification of matched items, discrepancies, and missing entries
- **Reconciliation History**: Track past reconciliation activities

### Key Components

- **DocumentUpload**: Component for uploading financial documents
- **ReconciliationProgress**: Visual indicator of reconciliation process
- **ReconciliationResults**: Display matched and unmatched items
- **ReconciliationHistory**: Table of past reconciliations with filtering

### Implementation

The reconciliation workflow follows these steps:

1. User uploads a document through the `DocumentUpload` component
2. User initiates reconciliation via the UI
3. Frontend establishes WebSocket connection to monitor progress
4. Backend processes the document and sends progress updates
5. UI displays real-time progress using the `ReconciliationProgress` component
6. Results are fetched and displayed in the `ReconciliationResults` component
7. User can export results or take corrective actions

### API Integration

```typescript
// Example of starting a reconciliation process
const startReconciliation = async (documentId: string) => {
  try {
    const response = await api.post('/supplier/reconciliation', {
      document_id: documentId,
    });
    
    return response.data;
  } catch (error) {
    console.error('Failed to start reconciliation:', error);
    throw error;
  }
};
```

## Inventory

The inventory interface provides real-time tracking of restaurant inventory levels, price changes, and usage analytics.

### Features

- **Restaurant Overview**: Health status indicators for all restaurant locations
- **Ingredient Analysis**: Price change monitoring and usage statistics
- **Threshold Alerts**: Configurable alerts for low inventory and price changes
- **Usage Analytics**: Data visualization of inventory consumption patterns

### Key Components

- **InventoryOverview**: Chain-wide inventory health dashboard
- **InventoryList**: Sortable, filterable list of inventory items
- **InventoryDetail**: Detailed view for individual inventory items
- **PriceChangeChart**: Visualization of price trends

### Implementation

The inventory system is implemented using:

1. TanStack Query for data fetching and caching
2. Recharts library for data visualizations
3. Status indicators (green/orange/red) for inventory health
4. Custom filters and sorting for inventory analysis

### API Integration

```typescript
// Example of fetching inventory status
const fetchInventoryStatus = async () => {
  try {
    const response = await api.get('/supplier/inventory/status');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch inventory status:', error);
    throw error;
  }
};

// Example of fetching price change history
const fetchPriceHistory = async (itemId: string) => {
  try {
    const response = await api.get(`/supplier/inventory/price-history/${itemId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch price history:', error);
    throw error;
  }
};
```

## Configuration

The AI Supplier module offers configurable settings:

- Reconciliation thresholds for automatic matching
- Inventory status thresholds (green/orange/red)
- Alert notification preferences
- Default view preferences

These settings can be managed through the Settings page within the application.

## Integration with Other Modules

The AI Supplier module integrates with:

- **AI Chef**: Inventory items are linked to menu items for cost analysis
- **Dashboard**: Key metrics from the Supplier module are displayed on the main dashboard

## Future Enhancements

Planned enhancements for the AI Supplier module include:

1. AI-powered predictive ordering
2. Supplier performance analytics
3. Enhanced visualization of inventory trends
4. Mobile scanning capabilities for inventory management