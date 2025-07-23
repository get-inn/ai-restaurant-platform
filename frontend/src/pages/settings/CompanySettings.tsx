
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Building2, MapPin, Globe, Clock, Users, CreditCard } from 'lucide-react';
import { useTranslation } from '@/contexts/TranslationContext';
import { useToast } from '@/hooks/use-toast';
import { useCurrency, CurrencyCode } from '@/contexts/CurrencyContext';

export default function CompanySettings() {
  const { t } = useTranslation();
  const { toast } = useToast();
  const { currency, setCurrency } = useCurrency();
  
  const [companyInfo, setCompanyInfo] = useState({
    name: 'GET INN Restaurant Group',
    description: 'Премиальная сеть ресторанов высокой кухни',
    website: 'https://getinn.com',
    phone: '+7 (495) 123-45-67',
    email: 'info@getinn.com',
    address: 'Москва, ул. Тверская, 12',
    timezone: 'Europe/Moscow',
    currency: 'RUB',
    industry: 'restaurant'
  });

  const [teamSettings, setTeamSettings] = useState({
    maxUsers: 50,
    currentUsers: 12,
    allowGuestAccess: false,
    requireTwoFactor: true,
    passwordPolicy: 'strong'
  });

  const [integrations, setIntegrations] = useState({
    pos: true,
    accounting: false,
    inventory: true,
    hr: false
  });

  // Sync currency context with company info
  useEffect(() => {
    setCompanyInfo(prev => ({ ...prev, currency: currency }));
  }, [currency]);

  // Handle currency change
  const handleCurrencyChange = (value: string) => {
    const currencyCode = value as CurrencyCode;
    // Update both local state and global context
    setCompanyInfo({ ...companyInfo, currency: currencyCode });
    setCurrency(currencyCode);
  };

  const handleSaveCompanyInfo = () => {
    toast({
      title: t('common.success'),
      description: "Информация о компании обновлена",
    });
  };

  const handleSaveTeamSettings = () => {
    toast({
      title: t('common.success'),
      description: "Настройки команды сохранены",
    });
  };

  const handleSaveIntegrations = () => {
    toast({
      title: t('common.success'),
      description: "Настройки интеграций обновлены",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t('settings.company')}</h1>
        <p className="text-muted-foreground">Управление настройками организации и команды</p>
      </div>

      <div className="grid gap-6">
        {/* Company Information */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              <CardTitle>Информация о компании</CardTitle>
            </div>
            <CardDescription>
              Основные данные вашей организации
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="companyName">Название компании</Label>
                <Input
                  id="companyName"
                  value={companyInfo.name}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="industry">Отрасль</Label>
                <Select value={companyInfo.industry} onValueChange={(value) => setCompanyInfo({ ...companyInfo, industry: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="restaurant">Ресторанный бизнес</SelectItem>
                    <SelectItem value="retail">Розничная торговля</SelectItem>
                    <SelectItem value="hospitality">Гостиничный бизнес</SelectItem>
                    <SelectItem value="catering">Кейтеринг</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Описание</Label>
              <Textarea
                id="description"
                value={companyInfo.description}
                onChange={(e) => setCompanyInfo({ ...companyInfo, description: e.target.value })}
                rows={3}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="website">
                  <Globe className="h-4 w-4 inline mr-1" />
                  Веб-сайт
                </Label>
                <Input
                  id="website"
                  value={companyInfo.website}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, website: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="companyPhone">Телефон</Label>
                <Input
                  id="companyPhone"
                  value={companyInfo.phone}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, phone: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="address">
                <MapPin className="h-4 w-4 inline mr-1" />
                Адрес
              </Label>
              <Input
                id="address"
                value={companyInfo.address}
                onChange={(e) => setCompanyInfo({ ...companyInfo, address: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="timezone">
                  <Clock className="h-4 w-4 inline mr-1" />
                  Часовой пояс
                </Label>
                <Select value={companyInfo.timezone} onValueChange={(value) => setCompanyInfo({ ...companyInfo, timezone: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Europe/Moscow">Москва (UTC+3)</SelectItem>
                    <SelectItem value="Europe/Paris">Париж (UTC+1)</SelectItem>
                    <SelectItem value="America/New_York">Нью-Йорк (UTC-5)</SelectItem>
                    <SelectItem value="Asia/Tokyo">Токио (UTC+9)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="currency">{t('settings.company.currency')}</Label>
                <Select value={companyInfo.currency} onValueChange={handleCurrencyChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="RUB">{t('currency.RUB')}</SelectItem>
                    <SelectItem value="USD">{t('currency.USD')}</SelectItem>
                    <SelectItem value="EUR">{t('currency.EUR')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSaveCompanyInfo}>{t('settings.save')}</Button>
            </div>
          </CardContent>
        </Card>

        {/* Team Management */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              <CardTitle>Управление командой</CardTitle>
            </div>
            <CardDescription>
              Настройки пользователей и безопасности
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">{teamSettings.currentUsers}</div>
                <div className="text-sm text-muted-foreground">Активных пользователей</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-muted-foreground">{teamSettings.maxUsers}</div>
                <div className="text-sm text-muted-foreground">Максимально пользователей</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-green-600">{teamSettings.maxUsers - teamSettings.currentUsers}</div>
                <div className="text-sm text-muted-foreground">Доступно слотов</div>
              </div>
            </div>

            <Separator />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Гостевой доступ</Label>
                  <p className="text-sm text-muted-foreground">Разрешить временный доступ без регистрации</p>
                </div>
                <Switch
                  checked={teamSettings.allowGuestAccess}
                  onCheckedChange={(checked) => setTeamSettings({ ...teamSettings, allowGuestAccess: checked })}
                />
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Двухфакторная аутентификация</Label>
                  <p className="text-sm text-muted-foreground">Требовать 2FA для всех пользователей</p>
                </div>
                <Switch
                  checked={teamSettings.requireTwoFactor}
                  onCheckedChange={(checked) => setTeamSettings({ ...teamSettings, requireTwoFactor: checked })}
                />
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <Label>Политика паролей</Label>
                <Select value={teamSettings.passwordPolicy} onValueChange={(value) => setTeamSettings({ ...teamSettings, passwordPolicy: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Базовая (8+ символов)</SelectItem>
                    <SelectItem value="strong">Строгая (12+ символов, спецсимволы)</SelectItem>
                    <SelectItem value="enterprise">Корпоративная (16+ символов, регулярная смена)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSaveTeamSettings}>{t('settings.save')}</Button>
            </div>
          </CardContent>
        </Card>

        {/* Integrations */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              <CardTitle>Интеграции</CardTitle>
            </div>
            <CardDescription>
              Подключение внешних сервисов и систем
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <div className="font-medium">POS система</div>
                  <div className="text-sm text-muted-foreground">Подключение кассовой системы</div>
                </div>
                <div className="flex items-center gap-2">
                  {integrations.pos && <Badge variant="outline" className="text-green-600">Активно</Badge>}
                  <Switch
                    checked={integrations.pos}
                    onCheckedChange={(checked) => setIntegrations({ ...integrations, pos: checked })}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <div className="font-medium">Бухгалтерия</div>
                  <div className="text-sm text-muted-foreground">1С, МойСклад</div>
                </div>
                <div className="flex items-center gap-2">
                  {integrations.accounting && <Badge variant="outline" className="text-green-600">Активно</Badge>}
                  <Switch
                    checked={integrations.accounting}
                    onCheckedChange={(checked) => setIntegrations({ ...integrations, accounting: checked })}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <div className="font-medium">Управление складом</div>
                  <div className="text-sm text-muted-foreground">Автоматический учет остатков</div>
                </div>
                <div className="flex items-center gap-2">
                  {integrations.inventory && <Badge variant="outline" className="text-green-600">Активно</Badge>}
                  <Switch
                    checked={integrations.inventory}
                    onCheckedChange={(checked) => setIntegrations({ ...integrations, inventory: checked })}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <div className="font-medium">HR система</div>
                  <div className="text-sm text-muted-foreground">Управление персоналом</div>
                </div>
                <div className="flex items-center gap-2">
                  {integrations.hr && <Badge variant="outline" className="text-green-600">Активно</Badge>}
                  <Switch
                    checked={integrations.hr}
                    onCheckedChange={(checked) => setIntegrations({ ...integrations, hr: checked })}
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSaveIntegrations}>{t('settings.save')}</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
