
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { mockApi, OnboardingStaff } from '@/services/mockApi';
import { Users, GraduationCap, Calendar, TrendingUp, Building2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useTranslation } from '@/contexts/TranslationContext';

const Onboarding = () => {
  const { t } = useTranslation();
  const [staff, setStaff] = useState<OnboardingStaff[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOnboardingData = async () => {
      try {
        const data = await mockApi.getOnboardingStaff();
        setStaff(data);
      } catch (error) {
        console.error('Error fetching onboarding data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOnboardingData();
  }, []);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'in-progress': return 'secondary';
      case 'not-started': return 'outline';
      default: return 'outline';
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  // Calculate overview stats
  const overviewStats = staff.reduce((acc, member) => {
    const restaurant = acc.find(r => r.restaurantId === member.restaurantId);
    if (restaurant) {
      restaurant.totalStaff++;
      if (member.status === 'completed') restaurant.completed++;
      if (member.status === 'in-progress') restaurant.inProgress++;
      if (member.status === 'not-started') restaurant.notStarted++;
    } else {
      acc.push({
        restaurantId: member.restaurantId,
        restaurantName: member.restaurantName,
        totalStaff: 1,
        completed: member.status === 'completed' ? 1 : 0,
        inProgress: member.status === 'in-progress' ? 1 : 0,
        notStarted: member.status === 'not-started' ? 1 : 0
      });
    }
    return acc;
  }, [] as any[]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('onboarding.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">{t('pages.onboarding.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('pages.onboarding.subtitle')}
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="overview">{t('tabs.overview')}</TabsTrigger>
          <TabsTrigger value="details">{t('tabs.details')}</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Chain-wide Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t('onboarding.stats.totalStaff')}</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{staff.length}</div>
                <p className="text-xs text-muted-foreground">
                  {t('onboarding.stats.acrossLocations')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t('onboarding.stats.inProgress')}</CardTitle>
                <TrendingUp className="h-4 w-4 text-orange-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {staff.filter(s => s.status === 'in-progress').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  {t('onboarding.stats.currentlyTraining')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t('onboarding.stats.completed')}</CardTitle>
                <GraduationCap className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {staff.filter(s => s.status === 'completed').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  {t('onboarding.stats.readyToServe')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t('onboarding.stats.completionRate')}</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round((staff.filter(s => s.status === 'completed').length / staff.length) * 100)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {t('onboarding.stats.overallSuccess')}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Restaurant-wise Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                {t('onboarding.status.title')}
              </CardTitle>
              <CardDescription>
                {t('onboarding.status.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {overviewStats.map((restaurant) => (
                  <div
                    key={restaurant.restaurantId}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                        <Users className="w-5 h-5 text-primary-foreground" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground">{restaurant.restaurantName}</h3>
                        <p className="text-sm text-muted-foreground">
                          {restaurant.totalStaff} staff members
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <p className="text-sm font-medium text-green-600">{restaurant.completed}</p>
                        <p className="text-xs text-muted-foreground">{t('common.status.completed')}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-medium text-orange-600">{restaurant.inProgress}</p>
                        <p className="text-xs text-muted-foreground">{t('onboarding.details.status.inProgress')}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-medium text-muted-foreground">{restaurant.notStarted}</p>
                        <p className="text-xs text-muted-foreground">{t('onboarding.details.status.notStarted')}</p>
                      </div>
                      <div className="text-right">
                        <Progress 
                          value={(restaurant.completed / restaurant.totalStaff) * 100} 
                          className="w-32"
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                          {Math.round((restaurant.completed / restaurant.totalStaff) * 100)}% complete
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="details" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Staff Onboarding Details
              </CardTitle>
              <CardDescription>
                Individual staff member onboarding progress and timeline
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Staff Member</TableHead>
                    <TableHead>Restaurant</TableHead>
                    <TableHead>Position</TableHead>
                    <TableHead>Start Date</TableHead>
                    <TableHead>Exam Date</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {staff.map((member) => (
                    <TableRow key={member.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                              {getInitials(member.name)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium">{member.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>{member.restaurantName}</TableCell>
                      <TableCell>{member.position}</TableCell>
                      <TableCell>{new Date(member.startDate).toLocaleDateString()}</TableCell>
                      <TableCell>{new Date(member.plannedExamDate).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={member.currentProgress} className="w-20" />
                          <span className="text-sm text-muted-foreground">{member.currentProgress}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(member.status)}>
                          {member.status === 'not-started' ? t('onboarding.details.status.notStarted') : 
                           member.status === 'in-progress' ? t('onboarding.details.status.inProgress') : t('common.status.completed')}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Onboarding;
