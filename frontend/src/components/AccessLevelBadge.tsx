import { Globe, Building2, Lock, ShieldAlert } from 'lucide-react';
import type { AccessLevel } from '@/types';
import { cn } from '@/lib/utils';

const CONFIG: Record<AccessLevel, { icon: React.ElementType; label: string; cls: string }> = {
  public: { icon: Globe, label: 'Public', cls: 'border-green-600 text-green-700' },
  internal: { icon: Building2, label: 'Internal', cls: 'border-blue-600 text-blue-700' },
  confidential: { icon: Lock, label: 'Confidential', cls: 'border-amber-600 text-amber-700' },
  restricted: { icon: ShieldAlert, label: 'Restricted', cls: 'border-red-600 text-red-700' },
};

interface AccessLevelBadgeProps {
  level: AccessLevel;
  showLabel?: boolean;
  className?: string;
}

export function AccessLevelBadge({ level, showLabel = true, className }: AccessLevelBadgeProps) {
  const { icon: Icon, label, cls } = CONFIG[level] ?? CONFIG.public;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-xs font-medium',
        cls,
        className
      )}
    >
      <Icon className="h-3 w-3 shrink-0" />
      {showLabel && label}
    </span>
  );
}
