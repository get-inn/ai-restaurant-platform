
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatusBadge } from '@/components/ui/status-badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { mockApi, ReconciliationStatus, ReconciliationDocument } from '@/services/mockApi';
import { FileText, Upload, Clock, CheckCircle, AlertTriangle, Building2, Eye, Download } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useTranslation } from '@/contexts/TranslationContext';
import { useCurrency } from '@/contexts/CurrencyContext';

const Reconciliation = () => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrency();
  const [reconciliationStatus, setReconciliationStatus] = useState<ReconciliationStatus[]>([]);
  const [documents, setDocuments] = useState<ReconciliationDocument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusData, documentsData] = await Promise.all([
          mockApi.getReconciliationStatus(),
          mockApi.getReconciliationDocuments()
        ]);
        setReconciliationStatus(statusData);
        setDocuments(documentsData);
      } catch (error) {
        console.error('Error fetching reconciliation data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'processing': return 'secondary';
      case 'error': return 'destructive';
      default: return 'outline';
    }
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'in-progress': return <Clock className="h-4 w-4 text-orange-600" />;
      case 'error': return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default: return <div className="w-4 h-4 rounded-full border-2 border-muted-foreground/30" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('reconciliation.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">{t('pages.reconciliation.title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('pages.reconciliation.subtitle')}
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">{t('tabs.overview')}</TabsTrigger>
          <TabsTrigger value="documents">{t('tabs.documents')}</TabsTrigger>
          <TabsTrigger value="history">{t('tabs.history')}</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Chain-wide Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                {t('reconciliation.chainStatus.title')}
              </CardTitle>
              <CardDescription>
                {t('reconciliation.chainStatus.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {reconciliationStatus.map((status) => (
                  <div
                    key={status.restaurantId}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-primary-foreground" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground">{status.restaurantName}</h3>
                        <p className="text-sm text-muted-foreground">
                          {t('reconciliation.chainStatus.lastUpdated')}: {new Date(status.lastUpdate).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="text-sm font-medium">
                          {status.matchedItems}/{status.totalItems} {t('common.itemsMatched')}
                        </p>
                        <Progress 
                          value={(status.matchedItems / status.totalItems) * 100} 
                          className="w-32 mt-1"
                        />
                      </div>
                      
                      <div className="text-right">
                        <p className="text-sm font-medium text-orange-600">
                          {status.discrepancies} {t('common.discrepancies')}
                        </p>
                        <p className="text-xs text-muted-foreground">{t('reconciliation.chainStatus.needReview')}</p>
                      </div>
                      
                      <StatusBadge status={status.status} />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents" className="space-y-6">
          {/* Document Upload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                {t('reconciliation.documents.title')}
              </CardTitle>
              <CardDescription>
                {t('reconciliation.documents.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Upload Area */}
              <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:border-muted-foreground/50 transition-colors">
                <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">{t('reconciliation.documents.upload')}</h3>
                <p className="text-muted-foreground mb-4">
                  {t('reconciliation.documents.dragDrop')}
                </p>
                <Button>{t('reconciliation.documents.chooseFiles')}</Button>
                <p className="text-xs text-muted-foreground mt-2">
                  {t('reconciliation.documents.fileTypes')}
                </p>
              </div>

              {/* Document List */}
              <div>
                <h3 className="text-lg font-semibold mb-4">{t('reconciliation.documents.recent')}</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('reconciliation.documents.table.document')}</TableHead>
                      <TableHead>{t('reconciliation.documents.table.restaurant')}</TableHead>
                      <TableHead>{t('reconciliation.documents.table.supplier')}</TableHead>
                      <TableHead>{t('reconciliation.documents.table.amount')}</TableHead>
                      <TableHead>{t('reconciliation.documents.table.progress')}</TableHead>
                      <TableHead>{t('reconciliation.documents.table.status')}</TableHead>
                      <TableHead>{t('reconciliation.documents.table.actions')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{doc.filename}</p>
                            <p className="text-sm text-muted-foreground">
                              {new Date(doc.uploadDate).toLocaleDateString()}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>{doc.restaurantName}</TableCell>
                        <TableCell>{doc.supplier}</TableCell>
                        <TableCell>{formatCurrency(doc.totalAmount)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={(doc.currentStep / 8) * 100} className="w-20" />
                            <span className="text-sm text-muted-foreground">{doc.currentStep}/8</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(doc.status)}>
                            {t(`reconciliation.documents.status.${doc.status}`)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="icon">
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon">
                              <Download className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                {t('reconciliation.history.title')}
              </CardTitle>
              <CardDescription>
                {t('reconciliation.history.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-medium mb-2">{t('reconciliation.history.noData')}</h3>
                  <p>{t('reconciliation.history.noData')}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Reconciliation;
