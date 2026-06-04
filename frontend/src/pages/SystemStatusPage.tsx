import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, XCircle, RefreshCw, Database, Cpu } from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

interface HealthResponse {
  status: 'ok' | 'degraded';
  version: string;
  components: {
    database: 'ok' | 'unreachable';
    ollama: 'ok' | 'unreachable';
  };
}

function StatusIndicator({ status }: { status: 'ok' | 'unreachable' | undefined }) {
  if (!status) return <Skeleton className="h-5 w-5 rounded-full" />;
  return status === 'ok' ? (
    <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
  ) : (
    <XCircle className="h-5 w-5 text-destructive shrink-0" />
  );
}

function StatusText({ status }: { status: 'ok' | 'unreachable' | undefined }) {
  if (!status) return <Skeleton className="h-4 w-16" />;
  return (
    <span className={status === 'ok' ? 'text-green-700 font-medium' : 'text-destructive font-medium'}>
      {status === 'ok' ? 'Operational' : 'Unreachable'}
    </span>
  );
}

export function SystemStatusPage() {
  const { data, isLoading, dataUpdatedAt, refetch, isFetching } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: () => api.get('/health').then((r) => r.data),
    refetchInterval: 30_000,
    retry: false,
  });

  const overallOk = data?.status === 'ok';

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">System status</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Live health check of backend components.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Overall status banner */}
      <div
        className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
          isLoading
            ? 'bg-muted/30 border-border'
            : overallOk
            ? 'bg-green-50 border-green-200'
            : 'bg-destructive/10 border-destructive/30'
        }`}
      >
        {isLoading ? (
          <Skeleton className="h-6 w-6 rounded-full" />
        ) : overallOk ? (
          <CheckCircle2 className="h-6 w-6 text-green-600 shrink-0" />
        ) : (
          <XCircle className="h-6 w-6 text-destructive shrink-0" />
        )}
        <div>
          {isLoading ? (
            <Skeleton className="h-5 w-32" />
          ) : (
            <p className={`font-semibold ${overallOk ? 'text-green-800' : 'text-destructive'}`}>
              {overallOk ? 'All systems operational' : 'Degraded — one or more components unreachable'}
            </p>
          )}
          {dataUpdatedAt > 0 && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Last checked {new Date(dataUpdatedAt).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      {/* Component cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 font-medium">
              <Database className="h-4 w-4 text-muted-foreground" />
              PostgreSQL
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2">
              <StatusIndicator status={data?.components.database} />
              <StatusText status={data?.components.database} />
            </div>
            <p className="text-xs text-muted-foreground">
              Neon cloud PostgreSQL with pgvector extension. Stores documents, embeddings, users,
              and audit logs.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 font-medium">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              Ollama
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2">
              <StatusIndicator status={data?.components.ollama} />
              <StatusText status={data?.components.ollama} />
            </div>
            <p className="text-xs text-muted-foreground">
              Local LLM server. Runs <code className="text-xs bg-muted px-1 rounded">nomic-embed-text</code> for
              embeddings and <code className="text-xs bg-muted px-1 rounded">llama3.2:3b</code> for answer
              generation.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* API info */}
      {data && (
        <Card>
          <CardContent className="pt-4 pb-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">
                  API prefix
                </p>
                <code className="text-sm bg-muted px-2 py-0.5 rounded">{data.version}</code>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">
                  Overall status
                </p>
                <code className="text-sm bg-muted px-2 py-0.5 rounded">{data.status}</code>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
