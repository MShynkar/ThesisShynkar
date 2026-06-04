import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { Shield } from 'lucide-react';
import { authApi } from '@/api/endpoints';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function RegisterPage() {
  const navigate = useNavigate();
  const { setTokens } = useAuth();
  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      await authApi.register(form);
      return authApi.login(form.username, form.password);
    },
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      navigate('/chat');
    },
    onError: (e: AxiosError<{ detail: string }>) => {
      setError(e.response?.data?.detail || 'Registration failed');
    },
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <div className="flex justify-center">
            <Shield className="h-12 w-12 text-primary" />
          </div>
          <CardTitle>Create your account</CardTitle>
          <CardDescription>Join the document intelligence platform</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                minLength={3}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="full_name">Full name (optional)</Label>
              <Input
                id="full_name"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                minLength={8}
                required
              />
            </div>
            {error && (
              <div className="text-sm text-destructive bg-destructive/10 p-2 rounded-md">{error}</div>
            )}
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? 'Creating account…' : 'Create account'}
            </Button>
          </form>
          <p className="text-sm text-center text-muted-foreground mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
