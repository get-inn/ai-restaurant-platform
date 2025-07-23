import React, { createContext, useContext, useState, useEffect } from 'react';

// Define available currencies
export type CurrencyCode = 'RUB' | 'USD' | 'EUR';

// Currency symbols mapping
export const currencySymbols: Record<CurrencyCode, string> = {
  RUB: '₽',
  USD: '$',
  EUR: '€',
};

// Currency format configurations
export const currencyFormats: Record<CurrencyCode, Intl.NumberFormatOptions> = {
  RUB: { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 },
  USD: { style: 'currency', currency: 'USD', minimumFractionDigits: 2 },
  EUR: { style: 'currency', currency: 'EUR', minimumFractionDigits: 2 },
};

interface CurrencyContextType {
  currency: CurrencyCode;
  setCurrency: (currency: CurrencyCode) => void;
  formatCurrency: (amount: number) => string;
  currencySymbol: string;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

export const CurrencyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currency, setCurrency] = useState<CurrencyCode>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('currency') as CurrencyCode) || 'RUB';
    }
    return 'RUB';
  });

  useEffect(() => {
    localStorage.setItem('currency', currency);
  }, [currency]);

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('ru-RU', currencyFormats[currency]).format(amount);
  };

  return (
    <CurrencyContext.Provider 
      value={{ 
        currency, 
        setCurrency, 
        formatCurrency, 
        currencySymbol: currencySymbols[currency] 
      }}
    >
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = () => {
  const context = useContext(CurrencyContext);
  if (context === undefined) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
};