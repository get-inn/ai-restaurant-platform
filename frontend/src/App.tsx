
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { TranslationProvider } from "@/contexts/TranslationContext";
import { CurrencyProvider } from "@/contexts/CurrencyContext";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Header } from "@/components/layout/Header";
import Dashboard from "@/pages/Dashboard";
import Reconciliation from "@/pages/supplier/Reconciliation";
import Inventory from "@/pages/supplier/Inventory";
import Onboarding from "@/pages/labor/Onboarding";
import Menu from "@/pages/chef/Menu";
import UserSettings from "@/pages/settings/UserSettings";
import CompanySettings from "@/pages/settings/CompanySettings";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TranslationProvider>
      <CurrencyProvider>
        <ThemeProvider>
          <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <SidebarProvider>
              <div className="min-h-screen flex w-full bg-background">
                <AppSidebar />
                <div className="flex-1 flex flex-col">
                  <Header />
                  <main className="flex-1 p-6 custom-scrollbar overflow-auto">
                    <div className="max-w-7xl mx-auto">
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/supplier/reconciliation" element={<Reconciliation />} />
                        <Route path="/supplier/inventory" element={<Inventory />} />
                        <Route path="/labor/onboarding" element={<Onboarding />} />
                        <Route path="/chef/menu" element={<Menu />} />
                        <Route path="/settings/user" element={<UserSettings />} />
                        <Route path="/settings/company" element={<CompanySettings />} />
                        <Route path="*" element={<NotFound />} />
                      </Routes>
                    </div>
                  </main>
                </div>
              </div>
            </SidebarProvider>
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
      </CurrencyProvider>
    </TranslationProvider>
  </QueryClientProvider>
);

export default App;
