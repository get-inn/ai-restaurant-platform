
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Languages, User, Bell, Shield, Mail, Phone } from 'lucide-react';
import { useTranslation } from '@/contexts/TranslationContext';
import { useToast } from '@/hooks/use-toast';

export default function UserSettings() {
  const { language, setLanguage, t } = useTranslation();
  const { toast } = useToast();
  
  const [profile, setProfile] = useState({
    name: 'Иван Петров',
    email: 'ivan.petrov@getinn.com',
    phone: '+7 (495) 123-45-67',
    position: 'Менеджер ресторана',
    department: 'Операции'
  });

  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    sms: false,
    reports: true
  });

  const [privacy, setPrivacy] = useState({
    profileVisibility: 'team',
    activityLog: true,
    dataSharing: false
  });

  const handleSaveProfile = () => {
    toast({
      title: t('common.success'),
      description: "Профиль успешно обновлен",
    });
  };

  const handleSaveNotifications = () => {
    toast({
      title: t('common.success'),
      description: "Настройки уведомлений сохранены",
    });
  };

  const handleSavePrivacy = () => {
    toast({
      title: t('common.success'),
      description: "Настройки конфиденциальности сохранены",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t('settings.user')}</h1>
        <p className="text-muted-foreground">Управление профилем и персональными настройками</p>
      </div>

      <div className="grid gap-6">
        {/* Profile Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5" />
              <CardTitle>Профиль пользователя</CardTitle>
            </div>
            <CardDescription>
              Основная информация о вашем профиле
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4">
              <Avatar className="h-20 w-20">
                <AvatarImage src="/placeholder-avatar.jpg" />
                <AvatarFallback className="text-lg">ИП</AvatarFallback>
              </Avatar>
              <div className="space-y-2">
                <Button variant="outline" size="sm">Изменить фото</Button>
                <p className="text-sm text-muted-foreground">JPG, GIF или PNG. Максимум 1MB.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Полное имя</Label>
                <Input
                  id="name"
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="position">Должность</Label>
                <Input
                  id="position"
                  value={profile.position}
                  onChange={(e) => setProfile({ ...profile, position: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Телефон</Label>
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="phone"
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSaveProfile}>{t('settings.save')}</Button>
            </div>
          </CardContent>
        </Card>

        {/* Language Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Languages className="h-5 w-5" />
              <CardTitle>{t('settings.language')}</CardTitle>
            </div>
            <CardDescription>
              Выберите предпочитаемый язык интерфейса
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Язык интерфейса</Label>
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ru">{t('lang.ru')}</SelectItem>
                    <SelectItem value="en">{t('lang.en')}</SelectItem>
                    <SelectItem value="fr">{t('lang.fr')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <p className="text-sm text-muted-foreground">
                Язык интерфейса изменится автоматически после выбора
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Notifications Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              <CardTitle>{t('settings.notifications')}</CardTitle>
            </div>
            <CardDescription>
              Настройте способы получения уведомлений
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email уведомления</Label>
                  <p className="text-sm text-muted-foreground">Получать уведомления на email</p>
                </div>
                <Switch
                  checked={notifications.email}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, email: checked })}
                />
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Push уведомления</Label>
                  <p className="text-sm text-muted-foreground">Уведомления в браузере</p>
                </div>
                <Switch
                  checked={notifications.push}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, push: checked })}
                />
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>SMS уведомления</Label>
                  <p className="text-sm text-muted-foreground">Важные уведомления по SMS</p>
                </div>
                <Switch
                  checked={notifications.sms}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, sms: checked })}
                />
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Еженедельные отчеты</Label>
                  <p className="text-sm text-muted-foreground">Сводка активности за неделю</p>
                </div>
                <Switch
                  checked={notifications.reports}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, reports: checked })}
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSaveNotifications}>{t('settings.save')}</Button>
            </div>
          </CardContent>
        </Card>

        {/* Privacy Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              <CardTitle>{t('settings.privacy')}</CardTitle>
            </div>
            <CardDescription>
              Управление конфиденциальностью и безопасностью
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Видимость профиля</Label>
                <Select value={privacy.profileVisibility} onValueChange={(value) => setPrivacy({ ...privacy, profileVisibility: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">Всем пользователям</SelectItem>
                    <SelectItem value="team">Только команде</SelectItem>
                    <SelectItem value="private">Только мне</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Журнал активности</Label>
                  <p className="text-sm text-muted-foreground">Сохранять историю действий</p>
                </div>
                <Switch
                  checked={privacy.activityLog}
                  onCheckedChange={(checked) => setPrivacy({ ...privacy, activityLog: checked })}
                />
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Передача данных</Label>
                  <p className="text-sm text-muted-foreground">Разрешить передачу анонимных данных</p>
                </div>
                <Switch
                  checked={privacy.dataSharing}
                  onCheckedChange={(checked) => setPrivacy({ ...privacy, dataSharing: checked })}
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSavePrivacy}>{t('settings.save')}</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
