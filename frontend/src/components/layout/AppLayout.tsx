import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LogOut, FileText, MessageSquare, History, Settings, Search, Activity } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { authApi } from '@/api/endpoints';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Role } from '@/types';

const ROLE_VARIANT: Record<Role, 'role-admin' | 'role-manager' | 'role-user' | 'role-guest'> = {
  admin: 'role-admin',
  manager: 'role-manager',
  user: 'role-user',
  guest: 'role-guest',
};

export function AppLayout() {
  const navigate = useNavigate();
  const { user, accessToken, setUser, logout } = useAuth();

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    enabled: !!accessToken && !user,
    retry: false,
  });

  useEffect(() => {
    if (me) setUser(me);
  }, [me, setUser]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!accessToken) {
    navigate('/login');
    return null;
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
      isActive
        ? 'bg-primary text-primary-foreground'
        : 'text-muted-foreground hover:text-foreground hover:bg-accent'
    );

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="sticky top-0 z-10 border-b bg-white">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2 shrink-0">
              <Search className="h-5 w-5 text-primary" />
              <span className="font-semibold text-base tracking-tight">DocSearch</span>
            </Link>
            <nav className="flex items-center gap-0.5">
              <NavLink to="/chat" className={navLinkClass}>
                <MessageSquare className="h-4 w-4" />
                Search
              </NavLink>
              <NavLink to="/documents" className={navLinkClass}>
                <FileText className="h-4 w-4" />
                Documents
              </NavLink>
              <NavLink to="/history" className={navLinkClass}>
                <History className="h-4 w-4" />
                History
              </NavLink>
              {user?.role === 'admin' && (
                <>
                  <NavLink to="/admin" className={navLinkClass}>
                    <Settings className="h-4 w-4" />
                    Admin
                  </NavLink>
                  <NavLink to="/status" className={navLinkClass}>
                    <Activity className="h-4 w-4" />
                    Status
                  </NavLink>
                </>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {user && (
              <>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground hidden sm:block">
                    {user.full_name || user.username}
                  </span>
                  <Badge variant={ROLE_VARIANT[user.role]}>{user.role}</Badge>
                </div>
                <Button variant="ghost" size="sm" onClick={handleLogout} title="Sign out">
                  <LogOut className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 container py-6">
        <Outlet />
      </main>
    </div>
  );
}
