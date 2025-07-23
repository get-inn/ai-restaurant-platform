# AI Chef Module

The AI Chef module provides restaurant management tools for menu optimization, recipe management, and food cost analysis, helping restaurants maximize profitability and customer satisfaction.

## Overview

The AI Chef module focuses on menu performance analysis and recipe management with these primary features:

1. ABC menu analysis for sales and profitability
2. Recipe management and costing
3. Food cost optimization suggestions
4. Menu item performance tracking

## Key Components

### Menu Analysis Dashboard

The main interface for the AI Chef module includes:

- **ABC Analysis Chart**: Visual categorization of menu items by performance
- **Performance Metrics**: Sales volume, profit margin, and revenue statistics
- **Trend Indicators**: Changes in item performance over time
- **Filtering Controls**: Period selection and category filtering

### Recipe Management

The recipe interface provides:

- **Recipe List**: Searchable, filterable list of all recipes
- **Ingredient Breakdown**: Ingredients with quantities, units, and costs
- **Cost Calculation**: Automatic calculation of recipe cost
- **Yield Information**: Portions produced and per-portion cost
- **Preparation Instructions**: Step-by-step preparation guidelines

## ABC Menu Analysis

### Analysis Methodology

The ABC analysis categorizes menu items into performance groups:

- **Category A**: High profit and high sales (Stars)
- **Category B**: Medium profit or medium sales (Puzzles/Workhorses)
- **Category C**: Low profit and low sales (Dogs)
- **Category D**: Special items (Seasonal/Premium)

### Data Visualization

The analysis is presented using:

1. **Quadrant Chart**: X-axis for sales volume, Y-axis for profit margin
2. **Color Coding**: Visual indicators of item categories
3. **Tooltips**: Detailed metrics when hovering over items
4. **Filtering**: Options to focus on specific time periods or categories

### Implementation

```typescript
interface MenuItemAnalysis {
  id: string;
  name: string;
  category: string;
  abc_category: 'A' | 'B' | 'C' | 'D';
  profit_margin: number;
  sales_volume: number;
  revenue: number;
  cost: number;
  trend: 'up' | 'down' | 'stable';
}

// Example component for ABC analysis chart
function ABCAnalysisChart({ data, period }) {
  // Recharts implementation for quadrant visualization
  return (
    <div className="analysis-container">
      <h2>Menu ABC Analysis - {period}</h2>
      <div className="chart-controls">
        {/* Period selector and filters */}
      </div>
      <div className="quadrant-chart">
        <ScatterChart width={600} height={400}>
          <CartesianGrid />
          <XAxis type="number" dataKey="sales_volume" name="Sales Volume" />
          <YAxis type="number" dataKey="profit_margin" name="Profit Margin" />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Legend />
          <Scatter 
            name="Menu Items" 
            data={data} 
            fill="#8884d8"
            shape={renderCustomShape}
          />
          {/* Quadrant dividers */}
        </ScatterChart>
      </div>
      <div className="analysis-summary">
        {/* Summary metrics */}
      </div>
    </div>
  );
}
```

## Recipe Management

### Recipe Data Structure

```typescript
interface Recipe {
  id: string;
  name: string;
  description: string;
  category: string;
  yield_quantity: number;
  yield_unit: string;
  preparation_time: number;
  cooking_time: number;
  ingredients: Ingredient[];
  instructions: string[];
  cost_per_unit: number;
  selling_price: number;
  profit_margin: number;
}

interface Ingredient {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  cost: number;
  inventory_item_id: string;
}
```

### Key Features

1. **Recipe Editor**: Interactive form for creating and editing recipes
2. **Cost Calculator**: Automatic calculation as ingredients are added/modified
3. **Yield Adjuster**: Tools to scale recipe quantities
4. **Ingredient Linker**: Connection to inventory system for cost updates
5. **Image Upload**: Visual presentation of finished dishes

## API Integration

The module connects to these backend endpoints:

```typescript
// Fetch ABC menu analysis
const fetchMenuAnalysis = async (period: string, category?: string) => {
  const params = category ? `?category=${category}` : '';
  const { data } = await api.get(`/v1/api/chef/menu/abc-analysis/${period}${params}`);
  return data;
};

// Fetch all recipes
const fetchRecipes = async () => {
  const { data } = await api.get('/v1/api/chef/recipes');
  return data;
};

// Fetch a specific recipe
const fetchRecipe = async (recipeId: string) => {
  const { data } = await api.get(`/v1/api/chef/recipes/${recipeId}`);
  return data;
};

// Create or update a recipe
const saveRecipe = async (recipe: Recipe) => {
  if (recipe.id) {
    const { data } = await api.put(`/v1/api/chef/recipes/${recipe.id}`, recipe);
    return data;
  } else {
    const { data } = await api.post('/v1/api/chef/recipes', recipe);
    return data;
  }
};
```

## User Interactions

### Analyzing Menu Performance

1. User navigates to Menu Analysis in the AI Chef module
2. User selects analysis period (last month, quarter, year)
3. System displays the ABC analysis chart with item categorization
4. User can filter by food category or search specific items
5. User can drill down into individual item performance
6. System provides recommendations for menu optimization

### Managing Recipes

1. User navigates to Recipes section
2. User can search, filter, or browse the recipe list
3. User selects a recipe to view details or create a new recipe
4. Recipe editor allows modification of ingredients, quantities, instructions
5. Cost calculations update in real-time as changes are made
6. User saves recipe, which updates connected menu items

## Performance Optimizations

The Chef module implements several optimizations:

1. **Data Caching**: React Query caches analysis data to reduce API calls
2. **Virtualized Lists**: Recipe lists use virtualization for performance with large datasets
3. **Lazy Loading**: Detailed recipe information is loaded on demand
4. **Memoization**: Expensive calculations are memoized to prevent re-renders

## Integration with Other Modules

The AI Chef module integrates with:

- **AI Supplier**: Uses inventory data for ingredient costs and availability
- **Dashboard**: Key menu metrics are displayed on the main dashboard

## Future Enhancements

Planned improvements to the AI Chef module include:

1. **Predictive Analytics**: AI-powered sales forecasting for menu items
2. **Menu Engineering**: Automated menu layout optimization
3. **Seasonal Analysis**: Tracking item performance across seasons
4. **Competitor Analysis**: Market comparison for pricing and offering
5. **Customer Feedback Integration**: Incorporating review data into performance metrics

## Technical Implementation Notes

- Uses Recharts for data visualization
- Implements React Query for data fetching and caching
- Utilizes drag-and-drop for recipe instruction reordering
- Uses context API for module-wide state management