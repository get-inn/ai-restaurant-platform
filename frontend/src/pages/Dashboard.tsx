import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { mockApi, Restaurant, ReconciliationStatus } from '@/services/mockApi';
import { Badge } from '@/components/ui/badge';
import { Building2, TrendingUp, Users, ChefHat, AlertTriangle, CheckCircle } from 'lucide-react';
import { useTranslation } from '@/contexts/TranslationContext';

const Dashboard = () => {
  const { t } = useTranslation();
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [reconciliationStatus, setReconciliationStatus] = useState<ReconciliationStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [restaurantsData, reconciliationData] = await Promise.all([
          mockApi.getRestaurants(),
          mockApi.getReconciliationStatus()
        ]);
        setRestaurants(restaurantsData);
        setReconciliationStatus(reconciliationData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getStatusCounts = () => {
    const healthy = restaurants.filter(r => r.status === 'healthy').length;
    const warning = restaurants.filter(r => r.status === 'warning').length;
    const critical = restaurants.filter(r => r.status === 'critical').length;
    return { healthy, warning, critical };
  };

  const statusCounts = getStatusCounts();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('dashboard.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">{t('dashboard.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('dashboard.welcome')}
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.metrics.totalLocations.title')}</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{restaurants.length}</div>
            <p className="text-xs text-muted-foreground">{t('dashboard.metrics.totalLocations.description')}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.metrics.healthyStatus.title')}</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{statusCounts.healthy}</div>
            <p className="text-xs text-muted-foreground">{t('dashboard.metrics.healthyStatus.description')}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.metrics.needAttention.title')}</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{statusCounts.warning}</div>
            <p className="text-xs text-muted-foreground">{t('dashboard.metrics.needAttention.description')}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.metrics.criticalIssues.title')}</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{statusCounts.critical}</div>
            <p className="text-xs text-muted-foreground">{t('dashboard.metrics.criticalIssues.description')}</p>
          </CardContent>
        </Card>
      </div>

      {/* Restaurant Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {t('dashboard.restaurantOverview.title')}
          </CardTitle>
          <CardDescription>
            {t('dashboard.restaurantOverview.description')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {restaurants.map((restaurant) => {
              const reconciliation = reconciliationStatus.find(r => r.restaurantId === restaurant.id);
              return (
                <div
                  key={restaurant.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-navy-900 rounded-lg flex items-center justify-center">
                      <ChefHat className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">{restaurant.name}</h3>
                      <p className="text-sm text-muted-foreground">{restaurant.location}</p>
                      <p className="text-sm text-muted-foreground">{t('header.manager')}: {restaurant.manager}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {reconciliation && (
                      <div className="text-right">
                        <p className="text-sm font-medium">
                          {reconciliation.matchedItems}/{reconciliation.totalItems} {t('dashboard.restaurantOverview.items')}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {reconciliation.discrepancies} {t('dashboard.restaurantOverview.discrepancies')}
                        </p>
                      </div>
                    )}
                    <StatusBadge status={restaurant.status} />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="h-5 w-5 text-teal-600" />
              {t('dashboard.aiSupplier.title')}
            </CardTitle>
            <CardDescription>
              {t('dashboard.aiSupplier.description')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              {t('dashboard.aiSupplier.content')}
            </p>
            <div className="flex gap-2">
              <Badge variant="outline">{t('dashboard.aiSupplier.badge1')}</Badge>
              <Badge variant="outline">{t('dashboard.aiSupplier.badge2')}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Users className="h-5 w-5 text-teal-600" />
              {t('dashboard.aiLabor.title')}
            </CardTitle>
            <CardDescription>
              {t('dashboard.aiLabor.description')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              {t('dashboard.aiLabor.content')}
            </p>
            <div className="flex gap-2">
              <Badge variant="outline">{t('dashboard.aiLabor.badge1')}</Badge>
              <Badge variant="outline">{t('dashboard.aiLabor.badge2')}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ChefHat className="h-5 w-5 text-teal-600" />
              {t('dashboard.aiChef.title')}
            </CardTitle>
            <CardDescription>
              {t('dashboard.aiChef.description')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              {t('dashboard.aiChef.content')}
            </p>
            <div className="flex gap-2">
              <Badge variant="outline">{t('dashboard.aiChef.badge1')}</Badge>
              <Badge variant="outline">{t('dashboard.aiChef.badge2')}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;