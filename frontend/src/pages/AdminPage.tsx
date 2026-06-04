import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { Plus, Trash2, Loader2, Users, ScrollText, AlertCircle } from 'lucide-react';
import { adminApi } from '@/api/endpoints';
import type { Role, User } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Avatar } from '@/components/ui/avatar';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useAuth } from '@/lib/auth';

const ROLES: Role[] = ['admin', 'manager', 'user', 'guest'];

const ROLE_VARIANT: Record<Role, 'role-admin' | 'role-manager' | 'role-user' | 'role-guest'> = {
  admin: 'role-admin',
  manager: 'role-manager',
  user: 'role-user',
  guest: 'role-guest',
};

function TableSkeleton({ cols }: { cols: number }) {
  return (
    <>
      {[...Array(5)].map((_, i) => (
        <TableRow key={i}>
          {[...Array(cols)].map((_, j) => (
            <TableCell key={j}>
              <Skeleton className="h-4 w-full max-w-[120px]" />
            </TableCell>
          ))}
        </TableRow>
      ))}
    </>
  );
}

function CreateUserDialog() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    role: 'user' as Role,
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => adminApi.createUser(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      setOpen(false);
      setForm({ email: '', username: '', password: '', full_name: '', role: 'user' });
      setError(null);
    },
    onError: (e: AxiosError<{ detail: string }>) => {
      setError(e.response?.data?.detail || 'Failed to create user');
    },
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    mutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-4 w-4" />
          New user
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create user</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Email</Label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label>Username</Label>
              <Input
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>Full name</Label>
            <Input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Password</Label>
            <Input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              minLength={8}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </option>
              ))}
            </Select>
          </div>
          {error && (
            <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 p-2.5 rounded-md">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              {error}
            </div>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function UsersTab() {
  const qc = useQueryClient();
  const { user: me } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.listUsers(1, 100),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<{ role: Role; is_active: boolean }> }) =>
      adminApi.updateUser(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="h-4 w-4" />
          Users
          {data && (
            <span className="text-sm font-normal text-muted-foreground">({data.total})</span>
          )}
        </CardTitle>
        <CreateUserDialog />
      </CardHeader>
      <CardContent className="pt-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Active</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableSkeleton cols={6} />
            ) : (
              data?.items.map((u: User) => (
                <TableRow key={u.id}>
                  <TableCell>
                    <div className="flex items-center gap-2.5">
                      <Avatar name={u.full_name || u.username} size="sm" />
                      <span className="font-medium text-sm">{u.username}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-xs">{u.email}</TableCell>
                  <TableCell>
                    <Select
                      value={u.role}
                      disabled={u.id === me?.id}
                      onChange={(e) =>
                        updateMutation.mutate({ id: u.id, data: { role: e.target.value as Role } })
                      }
                      className="h-7 text-xs w-28"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={u.is_active}
                      onCheckedChange={(v) =>
                        updateMutation.mutate({ id: u.id, data: { is_active: v } })
                      }
                      disabled={u.id === me?.id}
                    />
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(u.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                      disabled={u.id === me?.id}
                      onClick={() => {
                        if (confirm(`Delete user "${u.username}"?`)) deleteMutation.mutate(u.id);
                      }}
                      title="Delete user"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function AuditTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['audit'],
    queryFn: () => adminApi.audit(1, 100),
  });

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ScrollText className="h-4 w-4" />
          Audit log
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>User ID</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Resource</TableHead>
              <TableHead>IP</TableHead>
              <TableHead>Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableSkeleton cols={6} />
            ) : (
              data?.items.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(entry.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {entry.user_id ? entry.user_id.slice(0, 8) : '—'}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono text-xs">
                      {entry.action}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {entry.resource_type
                      ? `${entry.resource_type}/${entry.resource_id?.slice(0, 8) ?? ''}`
                      : '—'}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {entry.ip_address || '—'}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground max-w-xs truncate">
                    {Object.keys(entry.details).length > 0
                      ? JSON.stringify(entry.details)
                      : '—'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export function AdminPage() {
  const [tab, setTab] = useState<'users' | 'audit'>('users');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Administration</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Manage users, roles, and review the system audit trail.
        </p>
      </div>

      <div className="flex gap-1 border-b">
        {(['users', 'audit'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors capitalize ${
              tab === t
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t === 'users' ? 'Users' : 'Audit log'}
          </button>
        ))}
      </div>

      {tab === 'users' ? <UsersTab /> : <AuditTab />}
    </div>
  );
}
