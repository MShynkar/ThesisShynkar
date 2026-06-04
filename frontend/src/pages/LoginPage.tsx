import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { Search, AlertCircle } from 'lucide-react';
import { authApi } from '@/api/endpoints';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Role } from '@/types';

const ROLE_VARIANT: Record<Role, 'role-admin' | 'role-manager' | 'role-user' | 'role-guest'> = {
  admin: 'role-admin',
  manager: 'role-manager',
  user: 'role-user',
  guest: 'role-guest',
};

const DEMO_ACCOUNTS = [
  { username: 'admin', password: 'admin123!', role: 'admin' as Role, access: 'All levels' },
  { username: 'manager', password: 'manager123!', role: 'manager' as Role, access: 'Public · Internal · Confidential' },
  { username: 'user', password: 'user123!', role: 'user' as Role, access: 'Public · Internal' },
  { username: 'guest', password: 'guest123!', role: 'guest' as Role, access: 'Public only' },
];

export function LoginPage() {
  const navigate = useNavigate();
  const { setTokens } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loginMutation = useMutation({
    mutationFn: () => authApi.login(username, password),
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      navigate('/chat');
    },
    onError: (e: AxiosError<{ detail: string }>) => {
      setError(e.response?.data?.detail || 'Login failed');
    },
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    loginMutation.mutate();
  };

  const fillCredentials = (acct: (typeof DEMO_ACCOUNTS)[0]) => {
    setUsername(acct.username);
    setPassword(acct.password);
    setError(null);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md space-y-4">
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
              <Search className="h-6 w-6 text-primary" />
            </div>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">DocSearch</h1>
          <p className="text-sm text-muted-foreground">Corporate document intelligence platform</p>
        </div>

        <Card className="shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Sign in</CardTitle>
            <CardDescription>Enter your credentials to access the system.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="username">Username or email</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="username"
                  autoComplete="username"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>
              {error && (
                <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 p-2.5 rounded-md">
                  <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                  {error}
                </div>
              )}
              <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
                {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>
            <p className="text-sm text-center text-muted-foreground mt-4">
              No account?{' '}
              <Link to="/register" className="text-primary hover:underline">
                Register
              </Link>
            </p>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardContent className="pt-4 pb-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Demo accounts — click to fill
            </p>
            <div className="divide-y divide-border rounded-md border overflow-hidden">
              {DEMO_ACCOUNTS.map((acct) => (
                <button
                  key={acct.username}
                  type="button"
                  onClick={() => fillCredentials(acct)}
                  className="w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-muted transition-colors text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <Badge variant={ROLE_VARIANT[acct.role]}>{acct.role}</Badge>
                    <span className="font-mono font-medium text-foreground">{acct.username}</span>
                  </div>
                  <span className="text-muted-foreground">{acct.access}</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
