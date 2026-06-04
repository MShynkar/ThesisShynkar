import { cn } from '@/lib/utils';

export function getInitials(name: string): string {
  const parts = name.trim().split(/[\s._@]+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

interface AvatarProps {
  name: string;
  size?: 'sm' | 'md';
  className?: string;
}

export function Avatar({ name, size = 'md', className }: AvatarProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center justify-center rounded-full bg-slate-200 font-medium text-slate-600 select-none shrink-0',
        size === 'sm' ? 'h-7 w-7 text-xs' : 'h-8 w-8 text-sm',
        className
      )}
      aria-label={name}
    >
      {getInitials(name)}
    </div>
  );
}
