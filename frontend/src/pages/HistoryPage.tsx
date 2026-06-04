import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Trash2, MessageSquare, History } from 'lucide-react';
import { searchApi } from '@/api/endpoints';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

function HistorySkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="border rounded-lg p-4 space-y-2">
          <div className="flex items-start justify-between gap-4">
            <Skeleton className="h-4 w-72" />
            <Skeleton className="h-4 w-8" />
          </div>
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-3 w-full max-w-sm" />
        </div>
      ))}
    </div>
  );
}

export function HistoryPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: () => searchApi.history(0, 100),
  });

  const deleteMutation = useMutation({
    mutationFn: searchApi.deleteHistory,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['history'] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Search history</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Your recent queries and the answers returned.
        </p>
      </div>

      {isLoading ? (
        <HistorySkeleton />
      ) : !data || data.length === 0 ? (
        <Card>
          <CardContent className="py-16 flex flex-col items-center gap-3 text-center text-muted-foreground">
            <History className="h-10 w-10 opacity-30" />
            <p className="font-medium">No search history</p>
            <p className="text-sm">Queries you make on the Search page will appear here.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {data.map((entry) => (
            <div
              key={entry.id}
              className="border rounded-lg px-4 py-3 bg-card hover:bg-muted/20 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5 min-w-0 flex-1">
                  <MessageSquare className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium leading-snug">{entry.query}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(entry.created_at).toLocaleString()} ·{' '}
                      {entry.result_count} source{entry.result_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 w-7 p-0 shrink-0 text-muted-foreground hover:text-destructive"
                  onClick={() => {
                    if (confirm('Delete this entry?')) deleteMutation.mutate(entry.id);
                  }}
                  title="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
              {entry.answer && (
                <p className="text-sm text-muted-foreground line-clamp-2 mt-2 pl-7">
                  {entry.answer}
                </p>
              )}
              {entry.sources && entry.sources.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 pl-7">
                  {entry.sources.slice(0, 4).map((s, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {s.document_title}
                    </Badge>
                  ))}
                  {entry.sources.length > 4 && (
                    <Badge variant="outline" className="text-xs text-muted-foreground">
                      +{entry.sources.length - 4} more
                    </Badge>
                  )}
                </div>
              )}
            </div>
          ))}
          <p className="text-xs text-muted-foreground pt-1">{data.length} entr{data.length !== 1 ? 'ies' : 'y'}</p>
        </div>
      )}
    </div>
  );
}
