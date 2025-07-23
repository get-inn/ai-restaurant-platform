
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { mockApi, MenuAnalysisItem, DateRange } from '@/services/mockApi';
import { ChefHat, TrendingUp, DollarSign, Star, BarChart3, Filter, ArrowUpDown, Search, CalendarIcon, ChevronDown } from 'lucide-react';
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth, startOfQuarter, endOfQuarter, subWeeks, subMonths, subQuarters } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { useTranslation } from '@/contexts/TranslationContext';
import { useCurrency } from '@/contexts/CurrencyContext';
import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

// Predefined date ranges
type DateRangeOption = 'this_week' | 'last_week' | 'this_month' | 'last_month' | 'this_quarter' | 'last_quarter' | 'custom';

const getDateRangeFromOption = (option: DateRangeOption): DateRange => {
  const now = new Date();
  
  switch (option) {
    case 'this_week':
      return { startDate: startOfWeek(now, { weekStartsOn: 1 }), endDate: now };
    case 'last_week':
      const lastWeek = subWeeks(now, 1);
      return { startDate: startOfWeek(lastWeek, { weekStartsOn: 1 }), endDate: endOfWeek(lastWeek, { weekStartsOn: 1 }) };
    case 'this_month':
      return { startDate: startOfMonth(now), endDate: now };
    case 'last_month':
      const lastMonth = subMonths(now, 1);
      return { startDate: startOfMonth(lastMonth), endDate: endOfMonth(lastMonth) };
    case 'this_quarter':
      return { startDate: startOfQuarter(now), endDate: now };
    case 'last_quarter':
      const lastQuarter = subQuarters(now, 1);
      return { startDate: startOfQuarter(lastQuarter), endDate: endOfQuarter(lastQuarter) };
    case 'custom':
      // Will be handled separately with custom date picker
      return { startDate: now, endDate: now };
    default:
      return { startDate: now, endDate: now };
  }
};

const Menu = () => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrency();
  const [menuItems, setMenuItems] = useState<MenuAnalysisItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<MenuAnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Date range filter state
  const [dateRangeOption, setDateRangeOption] = useState<DateRangeOption>('this_week');
  const [dateRange, setDateRange] = useState<DateRange>(getDateRangeFromOption('this_week'));
  const [customDateRange, setCustomDateRange] = useState<{
    from: Date | undefined;
    to: Date | undefined;
  }>({ from: undefined, to: undefined });
  const [isCustomDatePickerOpen, setIsCustomDatePickerOpen] = useState(false);
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [restaurantFilter, setRestaurantFilter] = useState<string[]>([]);
  const [profitRangeFilter, setProfitRangeFilter] = useState<string>('all'); // all, high, medium, low
  
  // Sort state
  const [sortField, setSortField] = useState<string>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // Available restaurants for filtering
  const [availableRestaurants, setAvailableRestaurants] = useState<{id: string, name: string}[]>([]);

  // Update date range when option changes
  useEffect(() => {
    if (dateRangeOption !== 'custom') {
      const newDateRange = getDateRangeFromOption(dateRangeOption);
      setDateRange(newDateRange);
    }
  }, [dateRangeOption]);
  
  // Update custom date range when calendar selection changes
  useEffect(() => {
    if (customDateRange.from && customDateRange.to) {
      setDateRange({
        startDate: customDateRange.from,
        endDate: customDateRange.to
      });
    }
  }, [customDateRange]);

  useEffect(() => {
    const fetchMenuData = async () => {
      try {
        setLoading(true);
        const data = await mockApi.getMenuAnalysis(dateRange);
        setMenuItems(data);
        setFilteredItems(data);
        
        // Extract unique restaurants for the filter
        const restaurants = Array.from(
          new Set(data.map(item => JSON.stringify({id: item.restaurantId, name: item.restaurantName})))
        ).map(item => JSON.parse(item));
        
        setAvailableRestaurants(restaurants);
      } catch (error) {
        console.error('Error fetching menu data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMenuData();
  }, [dateRange]);
  
  // Apply filters and sorting
  useEffect(() => {
    let result = [...menuItems];
    
    // Apply search filter
    if (searchQuery.trim() !== '') {
      const query = searchQuery.toLowerCase();
      result = result.filter(item => 
        item.name.toLowerCase().includes(query) || 
        item.restaurantName.toLowerCase().includes(query)
      );
    }
    
    // Apply category filter
    if (categoryFilter.length > 0) {
      result = result.filter(item => categoryFilter.includes(item.category));
    }
    
    // Apply restaurant filter
    if (restaurantFilter.length > 0) {
      result = result.filter(item => restaurantFilter.includes(item.restaurantId));
    }
    
    // Apply profit range filter
    if (profitRangeFilter !== 'all') {
      switch (profitRangeFilter) {
        case 'high': 
          result = result.filter(item => item.profitMargin >= 60);
          break;
        case 'medium':
          result = result.filter(item => item.profitMargin >= 40 && item.profitMargin < 60);
          break;
        case 'low':
          result = result.filter(item => item.profitMargin < 40);
          break;
      }
    }
    
    // Apply sorting
    result.sort((a, b) => {
      let fieldA: any = a[sortField as keyof MenuAnalysisItem];
      let fieldB: any = b[sortField as keyof MenuAnalysisItem];
      
      // String comparison
      if (typeof fieldA === 'string' && typeof fieldB === 'string') {
        return sortOrder === 'asc' 
          ? fieldA.localeCompare(fieldB) 
          : fieldB.localeCompare(fieldA);
      }
      
      // Number comparison
      return sortOrder === 'asc' ? fieldA - fieldB : fieldB - fieldA;
    });
    
    setFilteredItems(result);
  }, [menuItems, searchQuery, categoryFilter, restaurantFilter, profitRangeFilter, sortField, sortOrder]);
  
  // Handle sort toggle
  const handleSortChange = (value: string) => {
    const [field, order] = value.split('-');
    setSortField(field);
    setSortOrder(order as 'asc' | 'desc');
  };
  
  // Toggle filter item selection
  const toggleCategoryFilter = (category: string) => {
    if (categoryFilter.includes(category)) {
      setCategoryFilter(categoryFilter.filter(c => c !== category));
    } else {
      setCategoryFilter([...categoryFilter, category]);
    }
  };
  
  const toggleRestaurantFilter = (id: string) => {
    if (restaurantFilter.includes(id)) {
      setRestaurantFilter(restaurantFilter.filter(r => r !== id));
    } else {
      setRestaurantFilter([...restaurantFilter, id]);
    }
  };
  
  // Format date range for display
  const formatDateRange = (dateRange: DateRange): string => {
    return `${format(dateRange.startDate, 'dd.MM.yyyy')} - ${format(dateRange.endDate, 'dd.MM.yyyy')}`;
  };
  
  // Handle date range option change
  const handleDateRangeChange = (option: DateRangeOption) => {
    setDateRangeOption(option);
    if (option !== 'custom') {
      // Close custom picker if it's open
      setIsCustomDatePickerOpen(false);
    } else {
      // Open custom date picker
      setIsCustomDatePickerOpen(true);
    }
  };
  
  // Apply custom date range
  const applyCustomDateRange = () => {
    if (customDateRange.from && customDateRange.to) {
      setDateRange({
        startDate: customDateRange.from,
        endDate: customDateRange.to
      });
      setIsCustomDatePickerOpen(false);
    }
  };
  
  // Cancel custom date selection
  const cancelCustomDateRange = () => {
    setIsCustomDatePickerOpen(false);
    if (dateRangeOption === 'custom' && (!customDateRange.from || !customDateRange.to)) {
      // Revert to default if custom was selected but no valid dates were chosen
      setDateRangeOption('this_week');
    }
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setCategoryFilter([]);
    setRestaurantFilter([]);
    setProfitRangeFilter('all');
    setSortField('name');
    setSortOrder('asc');
    // Don't reset date range as it's a primary control
  };

  const getCategoryBadgeVariant = (category: string) => {
    switch (category) {
      case 'A': return 'default';
      case 'B': return 'secondary';
      case 'C': return 'outline';
      default: return 'outline';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'A': return 'text-green-600';
      case 'B': return 'text-orange-600';
      case 'C': return 'text-red-600';
      default: return 'text-muted-foreground';
    }
  };

  // Calculate summary stats from filtered items
  const totalRevenue = filteredItems.reduce((sum, item) => sum + item.revenue, 0);
  const avgProfitMargin = filteredItems.length > 0 ? 
    filteredItems.reduce((sum, item) => sum + item.profitMargin, 0) / filteredItems.length : 0;
  const categoryStats = {
    A: filteredItems.filter(item => item.category === 'A').length,
    B: filteredItems.filter(item => item.category === 'B').length,
    C: filteredItems.filter(item => item.category === 'C').length
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('menu.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">{t('pages.menu.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('pages.menu.subtitle')}
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('menu.stats.totalRevenue')}</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalRevenue)}</div>
            <p className="text-xs text-muted-foreground">
              {t('menu.stats.acrossItems')}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('menu.stats.avgProfitMargin')}</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round(avgProfitMargin)}%</div>
            <p className="text-xs text-muted-foreground">
              {t('menu.stats.avgAcrossItems')}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('menu.stats.categoryAItems')}</CardTitle>
            <Star className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{categoryStats.A}</div>
            <p className="text-xs text-muted-foreground">
              {t('menu.stats.highPerformers')}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('menu.stats.totalMenuItems')}</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{menuItems.length}</div>
            <p className="text-xs text-muted-foreground">
              {t('menu.stats.underAnalysis')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* ABC Analysis Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ChefHat className="h-5 w-5" />
            {t('menu.analysis.title')}
          </CardTitle>
          <CardDescription>
            {t('menu.analysis.description')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Date Range Selection */}
          <div className="flex flex-wrap items-center gap-3 pb-4 mb-4 border-b">
            <div className="flex items-center gap-2 mr-2">
              <CalendarIcon className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">{t('inventory.filter.dateRange')}:</span>
            </div>
            
            <Select
              value={dateRangeOption}
              onValueChange={(value: DateRangeOption) => handleDateRangeChange(value)}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder={t('inventory.filter.dateRange')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="this_week">{t('inventory.filter.thisWeek')}</SelectItem>
                <SelectItem value="last_week">{t('inventory.filter.lastWeek')}</SelectItem>
                <SelectItem value="this_month">{t('inventory.filter.thisMonth')}</SelectItem>
                <SelectItem value="last_month">{t('inventory.filter.lastMonth')}</SelectItem>
                <SelectItem value="this_quarter">{t('inventory.filter.thisQuarter')}</SelectItem>
                <SelectItem value="last_quarter">{t('inventory.filter.lastQuarter')}</SelectItem>
                <SelectItem value="custom">{t('inventory.filter.custom')}</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Custom Date Range Picker */}
            <Popover open={isCustomDatePickerOpen} onOpenChange={setIsCustomDatePickerOpen}>
              <PopoverTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="gap-2"
                  disabled={dateRangeOption !== 'custom'}
                >
                  <span className="text-sm">{formatDateRange(dateRange)}</span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <div className="p-3">
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">{t('inventory.filter.customDateRange')}</h4>
                    <div className="flex flex-col gap-2">
                      <Calendar
                        mode="range"
                        selected={{
                          from: customDateRange.from,
                          to: customDateRange.to
                        }}
                        onSelect={setCustomDateRange as any}
                      />
                      <div className="flex justify-end gap-2 mt-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={cancelCustomDateRange}>
                          {t('inventory.filter.cancel')}
                        </Button>
                        <Button 
                          size="sm" 
                          onClick={applyCustomDateRange} 
                          disabled={!customDateRange.from || !customDateRange.to}>
                          {t('inventory.filter.apply')}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          <div className="flex flex-wrap gap-3 pb-4 mb-4 border-b">
            {/* Search input */}
            <div className="flex-grow max-w-xs">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t('menu.filter.search')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8"
                />
              </div>
            </div>
            
            {/* Category filter dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  <Filter className="h-4 w-4" />
                  {t('menu.filter.category')}
                  {categoryFilter.length > 0 && (
                    <Badge variant="secondary" className="ml-1">{categoryFilter.length}</Badge>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuLabel>{t('menu.filter.categoryLabel')}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuCheckboxItem
                  checked={categoryFilter.includes('A')}
                  onCheckedChange={() => toggleCategoryFilter('A')}
                >
                  <span className="font-medium text-green-600">{t('menu.filter.categoryA')}</span>
                </DropdownMenuCheckboxItem>
                <DropdownMenuCheckboxItem
                  checked={categoryFilter.includes('B')}
                  onCheckedChange={() => toggleCategoryFilter('B')}
                >
                  <span className="font-medium text-orange-600">{t('menu.filter.categoryB')}</span>
                </DropdownMenuCheckboxItem>
                <DropdownMenuCheckboxItem
                  checked={categoryFilter.includes('C')}
                  onCheckedChange={() => toggleCategoryFilter('C')}
                >
                  <span className="font-medium text-red-600">{t('menu.filter.categoryC')}</span>
                </DropdownMenuCheckboxItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            {/* Restaurant filter dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  <Filter className="h-4 w-4" />
                  {t('menu.filter.restaurant')}
                  {restaurantFilter.length > 0 && (
                    <Badge variant="secondary" className="ml-1">{restaurantFilter.length}</Badge>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuLabel>{t('menu.filter.restaurantLabel')}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {availableRestaurants.map((restaurant) => (
                  <DropdownMenuCheckboxItem
                    key={restaurant.id}
                    checked={restaurantFilter.includes(restaurant.id)}
                    onCheckedChange={() => toggleRestaurantFilter(restaurant.id)}
                  >
                    {restaurant.name}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            
            {/* Profit margin filter */}
            <Select
              value={profitRangeFilter}
              onValueChange={(value) => setProfitRangeFilter(value)}
            >
              <SelectTrigger className="gap-2 max-w-[180px]">
                <Filter className="h-4 w-4" />
                <SelectValue placeholder={t('menu.filter.profitMargin')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('menu.filter.allMargins')}</SelectItem>
                <SelectItem value="high">{t('menu.filter.highMargin')}</SelectItem>
                <SelectItem value="medium">{t('menu.filter.mediumMargin')}</SelectItem>
                <SelectItem value="low">{t('menu.filter.lowMargin')}</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Sort dropdown */}
            <Select
              value={`${sortField}-${sortOrder}`}
              onValueChange={handleSortChange}
            >
              <SelectTrigger className="gap-2 max-w-[180px]">
                <ArrowUpDown className="h-4 w-4" />
                <SelectValue placeholder={t('menu.sort.label')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name-asc">{t('menu.sort.nameAsc')}</SelectItem>
                <SelectItem value="name-desc">{t('menu.sort.nameDesc')}</SelectItem>
                <SelectItem value="revenue-desc">{t('menu.sort.revenueDesc')}</SelectItem>
                <SelectItem value="revenue-asc">{t('menu.sort.revenueAsc')}</SelectItem>
                <SelectItem value="profitMargin-desc">{t('menu.sort.profitDesc')}</SelectItem>
                <SelectItem value="profitMargin-asc">{t('menu.sort.profitAsc')}</SelectItem>
                <SelectItem value="popularityScore-desc">{t('menu.sort.popularityDesc')}</SelectItem>
                <SelectItem value="popularityScore-asc">{t('menu.sort.popularityAsc')}</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Clear filters button */}
            {(searchQuery || categoryFilter.length > 0 || restaurantFilter.length > 0 || 
             profitRangeFilter !== 'all' || sortField !== 'name' || sortOrder !== 'asc') && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="ml-auto">
                {t('menu.filter.clear')}
              </Button>
            )}
          </div>
          
          {/* Filter results summary */}
          <div className="mb-4">
            <p className="text-sm text-muted-foreground">
              {t('menu.filter.showing')} 
              <span className="font-medium">{filteredItems.length}</span> {t('menu.filter.of')} 
              <span className="font-medium">{menuItems.length}</span> {t('menu.filter.items')}.
            </p>
          </div>
          
          <div className="mb-4">
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>{t('menu.categoryA')}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                <span>{t('menu.categoryB')}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>{t('menu.categoryC')}</span>
              </div>
            </div>
          </div>
          
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('menu.item.name')}</TableHead>
                <TableHead>{t('menu.item.restaurant')}</TableHead>
                <TableHead>{t('menu.item.category')}</TableHead>
                <TableHead>{t('menu.item.revenue')}</TableHead>
                <TableHead>{t('menu.item.profitMargin')}</TableHead>
                <TableHead>{t('menu.item.sales')}</TableHead>
                <TableHead>{t('menu.item.popularity')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="font-medium">{item.name}</div>
                  </TableCell>
                  <TableCell>{item.restaurantName}</TableCell>
                  <TableCell>
                    <Badge variant={getCategoryBadgeVariant(item.category)}>
                      {t('menu.insights.categoryPrefix')} {item.category}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className={getCategoryColor(item.category)}>
                      {formatCurrency(item.revenue)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className={getCategoryColor(item.category)}>
                      {item.profitMargin}%
                    </span>
                  </TableCell>
                  <TableCell>{item.salesCount}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-12 bg-muted rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            item.category === 'A' ? 'bg-green-500' :
                            item.category === 'B' ? 'bg-orange-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${item.popularityScore}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground">{item.popularityScore}</span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* AI Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            {t('dashboard.aiChef.badge2')}
          </CardTitle>
          <CardDescription>
            {t('dashboard.aiChef.content')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-900/30 rounded-lg">
              <h4 className="font-semibold text-green-800 dark:text-green-400 mb-2">{t('menu.insights.categoryA')}</h4>
              <p className="text-sm text-green-700 dark:text-green-300">
                {t('menu.insights.categoryA.description')}
              </p>
            </div>
            
            <div className="p-4 bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-900/30 rounded-lg">
              <h4 className="font-semibold text-orange-800 dark:text-orange-400 mb-2">{t('menu.insights.categoryB')}</h4>
              <p className="text-sm text-orange-700 dark:text-orange-300">
                {t('menu.insights.categoryB.description')}
              </p>
            </div>
            
            <div className="p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-lg">
              <h4 className="font-semibold text-red-800 dark:text-red-400 mb-2">{t('menu.insights.categoryC')}</h4>
              <p className="text-sm text-red-700 dark:text-red-300">
                {t('menu.insights.categoryC.description')}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Menu;
