import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from '@/contexts/TranslationContext';
import {
  BarChart3,
  Building2,
  ChefHat,
  FileText,
  Home,
  Package,
  Settings,
  Truck,
  Users,
  CreditCard,
  User,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar,
} from '@/components/ui/sidebar';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

const getMenuItems = (t: (key: string) => string) => [
  {
    title: t('nav.dashboard'),
    url: '/',
    icon: Home,
  },
  {
    title: t('nav.supplier'),
    icon: Truck,
    items: [
      {
        title: t('nav.reconciliation'),
        url: '/supplier/reconciliation',
        icon: FileText,
      },
      {
        title: t('nav.inventory'),
        url: '/supplier/inventory',
        icon: Package,
      },
    ],
  },
  {
    title: t('nav.labor'),
    icon: Users,
    items: [
      {
        title: t('nav.onboarding'),
        url: '/labor/onboarding',
        icon: Users,
      },
    ],
  },
  {
    title: t('nav.chef'),
    icon: ChefHat,
    items: [
      {
        title: t('nav.menu'),
        url: '/chef/menu',
        icon: BarChart3,
      },
    ],
  },
];

const getSettingsItems = (t: (key: string) => string) => [
  {
    title: t('settings.user'),
    url: '/settings/user',
    icon: User,
  },
  {
    title: t('settings.company'),
    url: '/settings/company',
    icon: Building2,
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === 'collapsed';
  const location = useLocation();
  const currentPath = location.pathname;
  const { t } = useTranslation();

  const isActive = (path: string) => currentPath === path;
  const isParentActive = (items: any[]) => items.some(item => isActive(item.url));

  const getNavClassName = (active: boolean) =>
    active 
      ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium' 
      : 'hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground';

  return (
    <Sidebar className="border-r border-sidebar-border">
      <SidebarContent className="custom-scrollbar">
        {/* GET INN Application Logo */}
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg overflow-hidden bg-white p-1">
              <img 
                src="/uploads/48e2cdc5-2275-4a3a-bcae-5e8cf951bac5.png" 
                alt="GET INN Logo" 
                className="w-full h-full object-contain"
              />
            </div>
            {!collapsed && (
              <div>
                <h2 className="text-lg font-bold text-sidebar-foreground">GET INN</h2>
                <p className="text-xs text-sidebar-foreground/70">{t('app.tagline')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Main Navigation */}
        <SidebarGroup>
          <SidebarGroupLabel>{t('app.navigation')}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {getMenuItems(t).map((item) => (
                <SidebarMenuItem key={item.title}>
                  {item.items ? (
                    <Collapsible
                      defaultOpen={isParentActive(item.items)}
                      className="group/collapsible"
                    >
                      <CollapsibleTrigger asChild>
                        <SidebarMenuButton className="hover:bg-sidebar-accent/50">
                          <item.icon className="w-4 h-4" />
                          {!collapsed && (
                            <>
                              <span>{item.title}</span>
                              <ChevronRight className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90" />
                            </>
                          )}
                        </SidebarMenuButton>
                      </CollapsibleTrigger>
                      {!collapsed && (
                        <CollapsibleContent>
                          <SidebarMenuSub>
                            {item.items.map((subItem) => (
                              <SidebarMenuSubItem key={subItem.title}>
                                <SidebarMenuSubButton asChild>
                                  <NavLink
                                    to={subItem.url}
                                    className={getNavClassName(isActive(subItem.url))}
                                  >
                                    <subItem.icon className="w-4 h-4" />
                                    <span>{subItem.title}</span>
                                  </NavLink>
                                </SidebarMenuSubButton>
                              </SidebarMenuSubItem>
                            ))}
                          </SidebarMenuSub>
                        </CollapsibleContent>
                      )}
                    </Collapsible>
                  ) : (
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        className={getNavClassName(isActive(item.url))}
                      >
                        <item.icon className="w-4 h-4" />
                        {!collapsed && <span>{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  )}
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Settings */}
        <SidebarGroup>
          <SidebarGroupLabel>{t('nav.settings')}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {getSettingsItems(t).map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      className={getNavClassName(isActive(item.url))}
                    >
                      <item.icon className="w-4 h-4" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
