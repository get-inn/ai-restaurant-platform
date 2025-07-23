
import React from 'react';
import { cn } from '@/lib/utils';
import { useTranslation } from '@/contexts/TranslationContext';

interface StatusBadgeProps {
  status: 'healthy' | 'warning' | 'critical';
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  const { t } = useTranslation();
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'healthy':
        return {
          text: t('common.status.healthy'),
          className: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 border-green-200 dark:border-green-900/30'
        };
      case 'warning':
        return {
          text: t('common.status.warning'),
          className: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400 border-orange-200 dark:border-orange-900/30'
        };
      case 'critical':
        return {
          text: t('common.status.critical'),
          className: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400 border-red-200 dark:border-red-900/30'
        };
      default:
        return {
          text: t('common.status.unknown'),
          className: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400 border-gray-200 dark:border-gray-900/30'
        };
    }
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-2.5 py-1.5 text-sm',
    lg: 'px-3 py-2 text-base'
  };

  const config = getStatusConfig(status);

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        config.className,
        sizeClasses[size],
        className
      )}
    >
      <div className={cn(
        'w-2 h-2 rounded-full mr-2',
        status === 'healthy' && 'bg-green-500',
        status === 'warning' && 'bg-orange-500',
        status === 'critical' && 'bg-red-500'
      )} />
      {config.text}
    </span>
  );
}
