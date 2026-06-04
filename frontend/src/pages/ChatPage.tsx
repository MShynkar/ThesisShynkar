import { useState, type FormEvent, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { Send, FileText, Loader2, AlertCircle, Info, MessageSquare } from 'lucide-react';
import { searchApi } from '@/api/endpoints';
import type { SearchResponse, Source } from '@/types';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ChatTurn {
  id: string;
  query: string;
  response?: SearchResponse;
  error?: string;
  pending: boolean;
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const preview = source.content.slice(0, 240);
  const truncated = source.content.length > 240;
  const matchPct = Math.round(source.similarity * 100);

  return (
    <div className="border rounded-lg p-3 bg-muted/20 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Badge variant="secondary" className="shrink-0 font-mono">
            [{index + 1}]
          </Badge>
          <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="font-medium text-sm truncate">{source.document_title}</span>
        </div>
        <span
          className="text-xs font-medium shrink-0 tabular-nums"
          title="Similarity score"
          style={{ color: matchPct >= 70 ? '#16a34a' : matchPct >= 45 ? '#b45309' : '#64748b' }}
        >
          {matchPct}%
        </span>
      </div>
      <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
        {expanded || !truncated ? source.content : `${preview}…`}
      </p>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Chunk #{source.chunk_index}</span>
        {truncated && (
          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            className="text-xs text-primary hover:underline"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>
    </div>
  );
}

export function ChatPage() {
  const [input, setInput] = useState('');
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.4);
  const [hybrid, setHybrid] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const searchMutation = useMutation({ mutationFn: searchApi.query });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || searchMutation.isPending) return;

    const query = input.trim();
    const turnId = crypto.randomUUID();
    setTurns((prev) => [...prev, { id: turnId, query, pending: true }]);
    setInput('');

    try {
      const response = await searchMutation.mutateAsync({
        query,
        top_k: topK,
        threshold,
        hybrid,
        generate_answer: true,
      });
      setTurns((prev) =>
        prev.map((t) => (t.id === turnId ? { ...t, response, pending: false } : t))
      );
    } catch (err) {
      const e = err as AxiosError<{ detail: string }>;
      setTurns((prev) =>
        prev.map((t) =>
          t.id === turnId
            ? { ...t, pending: false, error: e.response?.data?.detail || 'Search failed' }
            : t
        )
      );
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_260px] gap-6 h-[calc(100vh-8rem)]">
      {/* ── Main chat area ── */}
      <div className="flex flex-col gap-4 min-h-0">
        <div className="flex-1 overflow-y-auto space-y-5 pr-1">
          {turns.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground pb-12">
              <MessageSquare className="h-10 w-10 mb-3 opacity-30" />
              <p className="font-medium text-base text-foreground">Ask a question</p>
              <p className="text-sm mt-1 max-w-sm">
                Search across corporate documents. Results are filtered by your access level.
              </p>
              <div className="mt-4 space-y-1 text-xs">
                <p className="text-muted-foreground/70">Try:</p>
                <p className="italic">"What is the vacation policy?"</p>
                <p className="italic">"Summarize the Q4 financial results"</p>
                <p className="italic">"Technical requirements for API integration"</p>
              </div>
            </div>
          )}

          {turns.map((turn) => (
            <div key={turn.id} className="space-y-3">
              {/* Query bubble */}
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-primary/10 border border-primary/20 rounded-lg px-4 py-2.5">
                  <p className="text-sm font-medium">{turn.query}</p>
                </div>
              </div>

              {/* Pending */}
              {turn.pending && (
                <div className="flex items-center gap-2 text-muted-foreground text-sm pl-1">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Searching and generating answer…
                </div>
              )}

              {/* Error */}
              {turn.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Search failed</AlertTitle>
                  <AlertDescription>{turn.error}</AlertDescription>
                </Alert>
              )}

              {/* Response */}
              {turn.response && (
                <div className="space-y-3">
                  {turn.response.answer && (
                    <div className="border-l-4 border-primary pl-4 py-1">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {turn.response.answer}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        {turn.response.sources.length} source
                        {turn.response.sources.length !== 1 ? 's' : ''} · {turn.response.elapsed_ms} ms
                      </p>
                    </div>
                  )}

                  {turn.response.sources.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                        Sources
                      </p>
                      {turn.response.sources.map((s, i) => (
                        <SourceCard key={s.chunk_id} source={s} index={i} />
                      ))}
                    </div>
                  ) : (
                    <Alert variant="info">
                      <Info className="h-4 w-4" />
                      <AlertTitle>No results found</AlertTitle>
                      <AlertDescription>
                        No information found in documents accessible to you. Try rephrasing your
                        query or adjusting the relevance threshold.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input form */}
        <form onSubmit={onSubmit} className="border-t pt-4 space-y-2">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents…"
              className="resize-none"
              rows={2}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  onSubmit(e as unknown as FormEvent);
                }
              }}
            />
            <Button
              type="submit"
              size="icon"
              className="self-end h-10 w-10"
              disabled={!input.trim() || searchMutation.isPending}
              title="Send (Ctrl+Enter)"
            >
              {searchMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">Press Ctrl+Enter to send</p>
        </form>
      </div>

      {/* ── Settings sidebar ── */}
      <aside className="space-y-5 lg:border-l lg:pl-6">
        <div>
          <h3 className="font-semibold text-sm">Search settings</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Adjust retrieval parameters</p>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="topk" className="text-xs">
              Top-K results
            </Label>
            <span className="text-xs font-mono text-muted-foreground">{topK}</span>
          </div>
          <input
            id="topk"
            type="range"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-full accent-primary"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>1</span>
            <span>20</span>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="threshold" className="text-xs">
              Relevance threshold
            </Label>
            <span className="text-xs font-mono text-muted-foreground">{threshold.toFixed(2)}</span>
          </div>
          <input
            id="threshold"
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="w-full accent-primary"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0.00</span>
            <span>1.00</span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3">
          <div>
            <Label htmlFor="hybrid" className="text-xs cursor-pointer">
              Hybrid search
            </Label>
            <p className="text-xs text-muted-foreground">Vector + full-text</p>
          </div>
          <Switch id="hybrid" checked={hybrid} onCheckedChange={setHybrid} />
        </div>

        <div className="border-t pt-4 space-y-1.5">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Access
          </p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Results are filtered to documents you have permission to view. Restricted documents are
            not visible to your role.
          </p>
        </div>
      </aside>
    </div>
  );
}
