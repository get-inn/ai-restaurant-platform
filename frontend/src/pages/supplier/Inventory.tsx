
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatusBadge } from '@/components/ui/status-badge';
import { mockApi, InventoryItem, Restaurant, WasteReason, DateRange } from '@/services/mockApi';
import { Package, TrendingUp, TrendingDown, AlertTriangle, Building2, Filter, ArrowUpDown, Trash2, Save, Pencil, CalendarIcon, ChevronDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useTranslation } from '@/contexts/TranslationContext';
import { useCurrency } from '@/contexts/CurrencyContext';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from '@/components/ui/use-toast';
import { Label } from '@/components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth, startOfQuarter, endOfQuarter, subWeeks, subMonths, subQuarters } from 'date-fns';

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

const Inventory = () => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrency();
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<InventoryItem[]>([]);
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(true);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [wasteReasons, setWasteReasons] = useState<WasteReason[]>([]);
  const [editingReasonId, setEditingReasonId] = useState<string | null>(null);
  const [editPercentageValue, setEditPercentageValue] = useState<string>('');
  
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
  const [statusFilter, setStatusFilter] = useState<string[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [restaurantFilter, setRestaurantFilter] = useState<string[]>([]);
  
  // Sort state
  const [sortField, setSortField] = useState<string>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // Available categories for filtering
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);

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

  // Fetch inventory data with date range
  useEffect(() => {
    const fetchInventoryData = async () => {
      try {
        setLoading(true);
        const [inventoryData, restaurantsData, wasteReasonData] = await Promise.all([
          mockApi.getInventoryItems(dateRange),
          mockApi.getRestaurants(),
          mockApi.getWasteReasons()
        ]);
        setInventoryItems(inventoryData);
        setFilteredItems(inventoryData);
        setWasteReasons(wasteReasonData);
        setRestaurants(restaurantsData);
        
        // Extract unique categories for the filter
        const categories = Array.from(new Set(inventoryData.map(item => item.category)));
        setAvailableCategories(categories);
      } catch (error) {
        console.error('Error fetching inventory data:', error);
      } finally {
        setLoading(false);
        setSettingsLoading(false);
      }
    };

    fetchInventoryData();
    
    // Fetch waste reasons for settings tab
    const fetchWasteReasons = async () => {
      try {
        const wasteReasonData = await mockApi.getWasteReasons();
        setWasteReasons(wasteReasonData);
      } catch (error) {
        console.error('Error fetching waste reason data:', error);
      } finally {
        setSettingsLoading(false);
      }
    };
    
    fetchWasteReasons();
  }, []);
  
  const startEditingReason = (reason: WasteReason) => {
    setEditingReasonId(reason.id);
    setEditPercentageValue(reason.allowedPercentage.toString());
  };
  
  const cancelEditingReason = () => {
    setEditingReasonId(null);
    setEditPercentageValue('');
  };
  
  const saveWasteReasonAllowance = async (reasonId: string) => {
    const percentValue = parseFloat(editPercentageValue);
    if (isNaN(percentValue) || percentValue < 0) {
      toast({
        title: t('inventory.settings.invalidPercentage'),
        description: t('inventory.settings.invalidPercentageDesc'),
        variant: 'destructive'
      });
      return;
    }
    
    try {
      const updatedReason = await mockApi.updateWasteReasonAllowance(reasonId, percentValue);
      setWasteReasons(wasteReasons.map(reason => 
        reason.id === reasonId ? updatedReason : reason
      ));
      setEditingReasonId(null);
      toast({
        title: t('inventory.settings.wasteReasonUpdated'),
        description: t('inventory.settings.wasteReasonUpdatedDesc'),
      });
    } catch (error) {
      console.error('Error updating waste reason allowance:', error);
      toast({
        title: t('inventory.settings.errorUpdating'),
        description: t('inventory.settings.errorUpdatingDesc'),
        variant: 'destructive'
      });
    }
  };
  
  // Check if waste is excessive (over allowed percentage)
  const isWasteExcessive = (item: InventoryItem): boolean => {
    if (!item.wastePercentage || !item.wasteReasonId) return false;
    
    const wasteReason = wasteReasons.find(reason => reason.id === item.wasteReasonId);
    return wasteReason ? item.wastePercentage > wasteReason.allowedPercentage : false;
  };
  
  // Apply filters and sorting
  useEffect(() => {
    let result = [...inventoryItems];
    
    // Apply search filter
    if (searchQuery.trim() !== '') {
      const query = searchQuery.toLowerCase();
      result = result.filter(item => 
        item.name.toLowerCase().includes(query) || 
        item.category.toLowerCase().includes(query)
      );
    }
    
    // Apply status filter
    if (statusFilter.length > 0) {
      result = result.filter(item => statusFilter.includes(item.status));
    }
    
    // Apply category filter
    if (categoryFilter.length > 0) {
      result = result.filter(item => categoryFilter.includes(item.category));
    }
    
    // Apply restaurant filter
    if (restaurantFilter.length > 0) {
      result = result.filter(item => restaurantFilter.includes(item.restaurantId));
    }
    
    // Apply sorting
    result.sort((a, b) => {
      let fieldA: any = a[sortField as keyof InventoryItem];
      let fieldB: any = b[sortField as keyof InventoryItem];
      
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
  }, [inventoryItems, searchQuery, statusFilter, categoryFilter, restaurantFilter, sortField, sortOrder]);
  
  // Handle sort toggle
  const handleSortChange = (field: string) => {
    if (field === sortField) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };
  
  // Toggle filter item selection
  const toggleStatusFilter = (status: string) => {
    if (statusFilter.includes(status)) {
      setStatusFilter(statusFilter.filter(s => s !== status));
    } else {
      setStatusFilter([...statusFilter, status]);
    }
  };
  
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
  
  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter([]);
    setCategoryFilter([]);
    setRestaurantFilter([]);
    setSortField('name');
    setSortOrder('asc');
    // Don't reset date range as it's a primary control
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

  // Update item status based on waste percentage
  const updateItemStatus = (item: InventoryItem): InventoryItem => {
    // If no waste data, just return the original item
    if (!item.wastePercentage || !item.wasteReasonId) return item;
    
    // Find the waste reason to get the allowed percentage
    const wasteReason = wasteReasons.find(reason => reason.id === item.wasteReasonId);
    if (!wasteReason) return item;
    
    // If waste percentage is higher than allowed, update status to warning if it's not already critical
    if (item.wastePercentage > wasteReason.allowedPercentage && item.status === 'healthy') {
      return { ...item, status: 'warning' };
    }
    
    return item;
  };
  
  const getInventoryStatusByRestaurant = () => {
    return restaurants.map(restaurant => {
      // Get all items for this restaurant
      let restaurantItems = inventoryItems.filter(item => item.restaurantId === restaurant.id);
      
      // Apply waste percentage status updates
      restaurantItems = restaurantItems.map(updateItemStatus);
      
      const criticalItems = restaurantItems.filter(item => item.status === 'critical').length;
      const warningItems = restaurantItems.filter(item => item.status === 'warning').length;
      
      let status: 'healthy' | 'warning' | 'critical' = 'healthy';
      if (criticalItems > 0) status = 'critical';
      else if (warningItems > 0) status = 'warning';

      return {
        ...restaurant,
        inventoryStatus: status,
        criticalItems,
        warningItems,
        totalItems: restaurantItems.length
      };
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('inventory.loading')}</p>
        </div>
      </div>
    );
  }

  const restaurantInventoryStatus = getInventoryStatusByRestaurant();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">{t('inventory.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('inventory.subtitle')}
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">{t('tabs.overview')}</TabsTrigger>
          <TabsTrigger value="ingredients">{t('tabs.ingredients')}</TabsTrigger>
          <TabsTrigger value="settings">{t('tabs.settings')}</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                {t('inventory.chainStatus.title')}
              </CardTitle>
              <CardDescription>
                {t('inventory.chainStatus.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {restaurantInventoryStatus.map((restaurant) => (
                  <div
                    key={restaurant.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-navy-900 rounded-lg flex items-center justify-center">
                        <Package className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground">{restaurant.name}</h3>
                        <p className="text-sm text-muted-foreground">{restaurant.location}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <p className="text-lg font-bold text-red-600">{restaurant.criticalItems}</p>
                        <p className="text-xs text-muted-foreground">{t('inventory.metrics.critical')}</p>
                      </div>
                      
                      <div className="text-center">
                        <p className="text-lg font-bold text-orange-600">{restaurant.warningItems}</p>
                        <p className="text-xs text-muted-foreground">{t('inventory.metrics.warning')}</p>
                      </div>
                      
                      <div className="text-center">
                        <p className="text-lg font-bold">{restaurant.totalItems}</p>
                        <p className="text-xs text-muted-foreground">{t('inventory.metrics.totalItems')}</p>
                      </div>
                      
                      <StatusBadge status={restaurant.inventoryStatus} />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ingredients" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                {t('inventory.ingredients.title')}
              </CardTitle>
              <CardDescription>
                {t('inventory.ingredients.description')}
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
                  <Input
                    placeholder={t('inventory.filter.search')}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full"
                  />
                </div>
                
                {/* Status filter dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="gap-2">
                      <Filter className="h-4 w-4" />
                      {t('inventory.filter.status')}
                      {statusFilter.length > 0 && (
                        <Badge variant="secondary" className="ml-1">{statusFilter.length}</Badge>
                      )}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    <DropdownMenuLabel>{t('inventory.filter.statusLabel')}</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuCheckboxItem
                      checked={statusFilter.includes('healthy')}
                      onCheckedChange={() => toggleStatusFilter('healthy')}
                    >
                      {t('inventory.status.healthy')}
                    </DropdownMenuCheckboxItem>
                    <DropdownMenuCheckboxItem
                      checked={statusFilter.includes('warning')}
                      onCheckedChange={() => toggleStatusFilter('warning')}
                    >
                      {t('inventory.status.warning')}
                    </DropdownMenuCheckboxItem>
                    <DropdownMenuCheckboxItem
                      checked={statusFilter.includes('critical')}
                      onCheckedChange={() => toggleStatusFilter('critical')}
                    >
                      {t('inventory.status.critical')}
                    </DropdownMenuCheckboxItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                
                {/* Category filter dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="gap-2">
                      <Filter className="h-4 w-4" />
                      {t('inventory.filter.category')}
                      {categoryFilter.length > 0 && (
                        <Badge variant="secondary" className="ml-1">{categoryFilter.length}</Badge>
                      )}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    <DropdownMenuLabel>{t('inventory.filter.categoryLabel')}</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {availableCategories.map((category) => (
                      <DropdownMenuCheckboxItem
                        key={category}
                        checked={categoryFilter.includes(category)}
                        onCheckedChange={() => toggleCategoryFilter(category)}
                      >
                        {category}
                      </DropdownMenuCheckboxItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
                
                {/* Restaurant filter dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="gap-2">
                      <Filter className="h-4 w-4" />
                      {t('inventory.filter.restaurant')}
                      {restaurantFilter.length > 0 && (
                        <Badge variant="secondary" className="ml-1">{restaurantFilter.length}</Badge>
                      )}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    <DropdownMenuLabel>{t('inventory.filter.restaurantLabel')}</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {restaurants.map((restaurant) => (
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
                
                {/* Sort dropdown */}
                <Select
                  value={`${sortField}-${sortOrder}`}
                  onValueChange={(value) => {
                    const [field, order] = value.split('-');
                    setSortField(field);
                    setSortOrder(order as 'asc' | 'desc');
                  }}
                >
                  <SelectTrigger className="gap-2 max-w-[180px]">
                    <ArrowUpDown className="h-4 w-4" />
                    <SelectValue placeholder={t('inventory.sort.label')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="name-asc">{t('inventory.sort.nameAsc')}</SelectItem>
                    <SelectItem value="name-desc">{t('inventory.sort.nameDesc')}</SelectItem>
                    <SelectItem value="price-asc">{t('inventory.sort.priceAsc')}</SelectItem>
                    <SelectItem value="price-desc">{t('inventory.sort.priceDesc')}</SelectItem>
                    <SelectItem value="currentStock-asc">{t('inventory.sort.stockAsc')}</SelectItem>
                    <SelectItem value="currentStock-desc">{t('inventory.sort.stockDesc')}</SelectItem>
                  </SelectContent>
                </Select>
                
                {/* Clear filters button */}
                {(searchQuery || statusFilter.length > 0 || categoryFilter.length > 0 || restaurantFilter.length > 0 || 
                 sortField !== 'name' || sortOrder !== 'asc') && (
                  <Button variant="ghost" size="sm" onClick={clearFilters} className="ml-auto">
                    {t('inventory.filter.clear')}
                  </Button>
                )}
              </div>
              
              {/* Filter results summary */}
              <div className="pb-4">
                <p className="text-sm text-muted-foreground">
                  {t('inventory.filter.showing')} 
                  <span className="font-medium">{filteredItems.length}</span> {t('inventory.filter.of')} 
                  <span className="font-medium">{inventoryItems.length}</span> {t('inventory.filter.items')}.
                </p>
              </div>
              
              <div className="space-y-4">
                {filteredItems.map((item) => {
                  const stockPercentage = (item.currentStock / item.recommendedLevel) * 100;
                  return (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center">
                          <Package className="w-6 h-6 text-muted-foreground" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground">{item.name}</h3>
                          <p className="text-sm text-muted-foreground">{item.category}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {item.dishUsageCount} {t('inventory.ingredients.dishes')}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {item.salesPercentage}% {t('inventory.ingredients.sales')}
                            </Badge>
                            {item.wastePercentage > 0 && (
                              <Badge 
                                variant="outline" 
                                className={`text-xs ${isWasteExcessive(item) ? 'border-red-500 text-red-500' : ''}`}
                              >
                                <Trash2 className="w-3 h-3 mr-1" />
                                {item.wastePercentage}% {t('inventory.ingredients.waste')}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6">
                        <div className="text-right w-48"> {/* Fixed width for alignment */}
                          <p className="text-sm font-medium">
                            {item.currentStock} / {item.recommendedLevel} {item.unit}
                            {item.wasteQuantity > 0 && (
                              <span className="text-xs text-muted-foreground ml-1">
                                ({t('inventory.ingredients.wasted')}: {item.wasteQuantity})
                              </span>
                            )}
                          </p>
                          <Progress value={Math.min(stockPercentage, 100)} className="w-24 mt-1" />
                        </div>
                        
                        <div className="text-right">
                          <p className="text-sm font-medium">{formatCurrency(item.price)}</p>
                          <div className="flex items-center gap-1">
                            {item.priceChange > 0 ? (
                              <TrendingUp className="w-3 h-3 text-red-500" />
                            ) : (
                              <TrendingDown className="w-3 h-3 text-green-500" />
                            )}
                            <span className={`text-xs ${item.priceChange > 0 ? 'text-red-500' : 'text-green-500'}`}>
                              {item.priceChange > 0 ? '+' : ''}{item.priceChange}%
                            </span>
                          </div>
                        </div>
                        
                        <StatusBadge status={item.status} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trash2 className="h-5 w-5" />
                {t('inventory.settings.wasteTitle')}
              </CardTitle>
              <CardDescription>
                {t('inventory.settings.wasteDescription')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {settingsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-muted-foreground">{t('common.loading')}</p>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="mb-4">
                    <p className="text-sm text-muted-foreground">
                      {t('inventory.settings.wasteInfo')}
                    </p>
                  </div>
                  
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t('inventory.settings.wasteReason')}</TableHead>
                        <TableHead className="w-[200px]">{t('inventory.settings.allowedPercentage')}</TableHead>
                        <TableHead className="w-[100px] text-right">{t('common.actions')}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {wasteReasons.map((reason) => (
                        <TableRow key={reason.id}>
                          <TableCell>
                            <div className="font-medium">{reason.name}</div>
                          </TableCell>
                          <TableCell>
                            {editingReasonId === reason.id ? (
                              <div className="flex items-center gap-2">
                                <Input 
                                  type="number" 
                                  value={editPercentageValue}
                                  onChange={(e) => setEditPercentageValue(e.target.value)}
                                  step="0.1"
                                  min="0"
                                  className="max-w-[100px]"
                                />
                                <span>%</span>
                              </div>
                            ) : (
                              <div>{reason.allowedPercentage}%</div>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            {editingReasonId === reason.id ? (
                              <div className="flex justify-end gap-2">
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  onClick={cancelEditingReason}
                                >
                                  {t('common.cancel')}
                                </Button>
                                <Button 
                                  size="sm"
                                  onClick={() => saveWasteReasonAllowance(reason.id)}
                                >
                                  <Save className="w-4 h-4 mr-1" />
                                  {t('common.save')}
                                </Button>
                              </div>
                            ) : (
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => startEditingReason(reason)}
                              >
                                <Pencil className="w-4 h-4 mr-1" />
                                {t('common.edit')}
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Inventory;
