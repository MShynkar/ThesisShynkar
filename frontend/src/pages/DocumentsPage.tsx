import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import {
  Plus,
  Trash2,
  FileText,
  RefreshCw,
  Loader2,
  AlertCircle,
  Pencil,
  FolderOpen,
} from 'lucide-react';
import { documentsApi } from '@/api/endpoints';
import type { AccessLevel, Document } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { AccessLevelBadge } from '@/components/AccessLevelBadge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

const ACCESS_LEVELS: AccessLevel[] = ['public', 'internal', 'confidential', 'restricted'];

function statusBadge(status: Document['status']) {
  switch (status) {
    case 'ready':
      return <Badge variant="success">Ready</Badge>;
    case 'processing':
      return <Badge variant="warning">Processing…</Badge>;
    case 'pending':
      return <Badge variant="outline">Pending</Badge>;
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>;
  }
}

function DocumentListSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="border rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between gap-4">
            <Skeleton className="h-4 w-56" />
            <Skeleton className="h-5 w-16" />
          </div>
          <Skeleton className="h-3 w-72" />
          <div className="flex gap-2">
            <Skeleton className="h-5 w-20" />
            <Skeleton className="h-5 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}

function UploadDialog({ onUploaded }: { onUploaded: () => void }) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [accessLevel, setAccessLevel] = useState<AccessLevel>('internal');
  const [category, setCategory] = useState('');
  const [tagsText, setTagsText] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('No file selected');
      return documentsApi.upload(file, {
        title: title || file.name,
        access_level: accessLevel,
        category: category || undefined,
        tags: tagsText
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      });
    },
    onSuccess: () => {
      setOpen(false);
      setFile(null);
      setTitle('');
      setCategory('');
      setTagsText('');
      setError(null);
      onUploaded();
    },
    onError: (e: AxiosError<{ detail: string }>) => {
      setError(e.response?.data?.detail || 'Upload failed');
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
        <Button>
          <Plus className="h-4 w-4" />
          Upload document
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload a document</DialogTitle>
          <DialogDescription>PDF, DOCX, TXT, or Markdown. Max 50 MB.</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="file">File</Label>
            <Input
              id="file"
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={file?.name || 'Document title'}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="access">Access level</Label>
            <Select
              id="access"
              value={accessLevel}
              onChange={(e) => setAccessLevel(e.target.value as AccessLevel)}
            >
              {ACCESS_LEVELS.map((lvl) => (
                <option key={lvl} value={lvl}>
                  {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="category">Category (optional)</Label>
            <Input
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. HR, Finance, Technical"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              value={tagsText}
              onChange={(e) => setTagsText(e.target.value)}
              placeholder="hr, policy, 2024"
            />
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
            <Button type="submit" disabled={!file || mutation.isPending}>
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Uploading…
                </>
              ) : (
                'Upload'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EditDialog({ doc, onClose }: { doc: Document; onClose: () => void }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState(doc.title);
  const [accessLevel, setAccessLevel] = useState<AccessLevel>(doc.access_level);
  const [category, setCategory] = useState(doc.category || '');
  const [tagsText, setTagsText] = useState(doc.tags.join(', '));

  const mutation = useMutation({
    mutationFn: () =>
      documentsApi.update(doc.id, {
        title,
        access_level: accessLevel,
        category: category || null,
        tags: tagsText
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] });
      onClose();
    },
  });

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit document</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <Label>Title</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Access level</Label>
            <Select
              value={accessLevel}
              onChange={(e) => setAccessLevel(e.target.value as AccessLevel)}
            >
              {ACCESS_LEVELS.map((lvl) => (
                <option key={lvl} value={lvl}>
                  {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Category</Label>
            <Input value={category} onChange={(e) => setCategory(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Tags</Label>
            <Input value={tagsText} onChange={(e) => setTagsText(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function DocumentRow({ doc, onEdit, onDelete, onReprocess, deletePending, reprocessPending }: {
  doc: Document;
  onEdit: () => void;
  onDelete: () => void;
  onReprocess: () => void;
  deletePending: boolean;
  reprocessPending: boolean;
}) {
  const sizeKb = (doc.file_size / 1024).toFixed(1);
  return (
    <div className="flex items-start gap-4 border rounded-lg px-4 py-3 bg-card hover:bg-muted/20 transition-colors">
      <FileText className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <span className="font-medium text-sm leading-tight">{doc.title}</span>
          <div className="flex items-center gap-2 shrink-0">
            {statusBadge(doc.status)}
            <AccessLevelBadge level={doc.access_level} />
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          {doc.filename} · {sizeKb} KB · {doc.chunk_count} chunks
          {doc.category && ` · ${doc.category}`}
        </p>
        {doc.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {doc.tags.map((t) => (
              <Badge key={t} variant="outline" className="text-xs">
                {t}
              </Badge>
            ))}
          </div>
        )}
        {doc.status === 'failed' && doc.error_message && (
          <p className="text-xs text-destructive bg-destructive/10 px-2 py-1 rounded">
            {doc.error_message}
          </p>
        )}
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <Button size="sm" variant="ghost" onClick={onEdit} title="Edit">
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={onReprocess}
          disabled={reprocessPending}
          title="Reprocess"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${reprocessPending ? 'animate-spin' : ''}`} />
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="text-destructive hover:text-destructive"
          onClick={onDelete}
          disabled={deletePending}
          title="Delete"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

export function DocumentsPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<Document | null>(null);
  const [ownedOnly, setOwnedOnly] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['documents', { ownedOnly }],
    queryFn: () => documentsApi.list({ owned_only: ownedOnly, page_size: 50 }),
    refetchInterval: (q) => {
      const docs = q.state.data?.items || [];
      return docs.some((d) => d.status === 'processing' || d.status === 'pending') ? 3000 : false;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });

  const reprocessMutation = useMutation({
    mutationFn: documentsApi.reprocess,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Documents</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Access control is enforced at search time based on your role.
          </p>
        </div>
        <UploadDialog onUploaded={() => refetch()} />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="owned"
          checked={ownedOnly}
          onChange={(e) => setOwnedOnly(e.target.checked)}
          className="h-4 w-4 rounded border-input accent-primary cursor-pointer"
        />
        <Label htmlFor="owned" className="cursor-pointer text-sm">
          Show only my documents
        </Label>
      </div>

      {isLoading ? (
        <DocumentListSkeleton />
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-16 flex flex-col items-center gap-3 text-center text-muted-foreground">
            <FolderOpen className="h-10 w-10 opacity-40" />
            <p className="font-medium">No documents yet</p>
            <p className="text-sm">Upload a document to get started with semantic search.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {data?.items.map((doc) => (
            <DocumentRow
              key={doc.id}
              doc={doc}
              onEdit={() => setEditing(doc)}
              onDelete={() => {
                if (confirm(`Delete "${doc.title}"?`)) deleteMutation.mutate(doc.id);
              }}
              onReprocess={() => reprocessMutation.mutate(doc.id)}
              deletePending={deleteMutation.isPending}
              reprocessPending={reprocessMutation.isPending}
            />
          ))}
          <p className="text-xs text-muted-foreground pt-1">
            {data?.items.length} document{data?.items.length !== 1 ? 's' : ''} · {data?.total} total
          </p>
        </div>
      )}

      {editing && <EditDialog doc={editing} onClose={() => setEditing(null)} />}
    </div>
  );
}
