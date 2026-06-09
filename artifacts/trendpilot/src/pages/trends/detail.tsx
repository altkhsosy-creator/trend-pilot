import { useParams, useLocation } from "wouter";
import {
  useGetTrend,
  useUpdateTrend,
  useDeleteTrend,
  useAddToWatchlist,
  getGetTrendQueryKey,
  getListTrendsQueryKey,
  getGetTrendsSummaryQueryKey,
  getGetTopTrendsQueryKey,
  getListWatchlistQueryKey,
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendStatusBadge } from "@/components/trend-status-badge";
import { cn } from "@/lib/utils";
import {
  ArrowUpRight,
  ArrowDownRight,
  ArrowLeft,
  Eye,
  Trash2,
  ExternalLink,
  Calendar,
  Tag,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function TrendDetail() {
  const params = useParams<{ id: string }>();
  const [, navigate] = useLocation();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const id = Number(params.id);

  const { data: trend, isLoading, isError } = useGetTrend(id, {
    query: { enabled: !!id && !isNaN(id), queryKey: getGetTrendQueryKey(id) },
  });

  const deleteTrend = useDeleteTrend({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getListTrendsQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetTrendsSummaryQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetTopTrendsQueryKey() });
        navigate("/trends");
        toast({ title: "Trend deleted" });
      },
    },
  });

  const addToWatchlist = useAddToWatchlist({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getListWatchlistQueryKey() });
        toast({ title: "Added to watchlist", description: "Signal is now being tracked." });
      },
    },
  });

  const updateTrend = useUpdateTrend({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetTrendQueryKey(id) });
        queryClient.invalidateQueries({ queryKey: getListTrendsQueryKey() });
        toast({ title: "Trend updated" });
      },
    },
  });

  if (isLoading) {
    return (
      <div className="flex-1 p-6 lg:p-8 space-y-6">
        <div className="flex items-center gap-3">
          <Skeleton className="h-9 w-24" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-10 w-80" />
          <Skeleton className="h-6 w-40" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-28 rounded-lg" />)}
        </div>
        <Skeleton className="h-40 rounded-lg" />
      </div>
    );
  }

  if (isError || !trend) {
    return (
      <div className="flex-1 p-6 lg:p-8 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="text-muted-foreground">Signal not found.</div>
          <Button variant="ghost" onClick={() => navigate("/trends")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Trends
          </Button>
        </div>
      </div>
    );
  }

  const scoreBar = Math.min(100, Math.max(0, trend.score));

  return (
    <div className="flex-1 p-6 lg:p-8 space-y-8 overflow-y-auto">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        className="gap-2 text-muted-foreground"
        onClick={() => navigate("/trends")}
      >
        <ArrowLeft className="h-4 w-4" />
        All Signals
      </Button>

      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-start gap-4 flex-wrap justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{trend.name}</h1>
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              <span className="font-mono text-xs text-muted-foreground uppercase tracking-widest bg-muted px-2 py-1 rounded">
                {trend.category}
              </span>
              <TrendStatusBadge status={trend.status} />
              {trend.source && (
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <ExternalLink className="h-3 w-3" />
                  {trend.source}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => addToWatchlist.mutate({ data: { trendId: trend.id } })}
              disabled={addToWatchlist.isPending}
            >
              <Eye className="h-4 w-4" />
              Watch
            </Button>
            <Button
              variant="destructive"
              size="sm"
              className="gap-2"
              onClick={() => deleteTrend.mutate({ id: trend.id })}
              disabled={deleteTrend.isPending}
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardHeader className="pb-1 pt-5 px-5">
            <CardTitle className="text-xs font-mono text-muted-foreground uppercase tracking-widest">Score</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-4xl font-bold font-mono tracking-tight">{trend.score.toFixed(1)}</div>
            <div className="mt-3 h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-700"
                style={{ width: `${scoreBar}%` }}
              />
            </div>
            <div className="text-xs text-muted-foreground mt-1 font-mono">out of 100</div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardHeader className="pb-1 pt-5 px-5">
            <CardTitle className="text-xs font-mono text-muted-foreground uppercase tracking-widest">Velocity</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className={cn(
              "text-4xl font-bold font-mono tracking-tight flex items-center gap-1",
              trend.velocity > 0 ? "text-emerald-500" : trend.velocity < 0 ? "text-rose-500" : "text-muted-foreground"
            )}>
              {trend.velocity > 0 ? <ArrowUpRight className="h-8 w-8" /> : trend.velocity < 0 ? <ArrowDownRight className="h-8 w-8" /> : null}
              {trend.velocity > 0 ? "+" : ""}{trend.velocity.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground mt-1 font-mono">period change</div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardHeader className="pb-1 pt-5 px-5">
            <CardTitle className="text-xs font-mono text-muted-foreground uppercase tracking-widest">Status</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="mt-1">
              <TrendStatusBadge status={trend.status} className="text-sm px-3 py-1" />
            </div>
            <div className="text-xs text-muted-foreground mt-3 font-mono">signal phase</div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardHeader className="pb-1 pt-5 px-5">
            <CardTitle className="text-xs font-mono text-muted-foreground uppercase tracking-widest">Tracked Since</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            <div className="text-lg font-semibold font-mono tracking-tight">
              {new Date(trend.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            </div>
            <div className="text-xs text-muted-foreground mt-1 font-mono">
              {new Date(trend.createdAt).getFullYear()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Description and tags */}
      <div className="grid lg:grid-cols-3 gap-6">
        {trend.description && (
          <Card className="lg:col-span-2 border-border/50 bg-card/50 backdrop-blur">
            <CardHeader className="border-b border-border/50 bg-muted/20 pb-3 pt-4 px-5">
              <CardTitle className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Signal Analysis</CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              <p className="text-foreground leading-relaxed">{trend.description}</p>
              {trend.source && (
                <div className="mt-4 pt-4 border-t border-border/50 flex items-center gap-2 text-sm text-muted-foreground">
                  <ExternalLink className="h-3.5 w-3.5 flex-shrink-0" />
                  <span>Source: <span className="text-foreground font-medium">{trend.source}</span></span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardHeader className="border-b border-border/50 bg-muted/20 pb-3 pt-4 px-5">
            <CardTitle className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Tags</CardTitle>
          </CardHeader>
          <CardContent className="p-5">
            {trend.tags?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {trend.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="gap-1.5 px-2.5 py-1 text-sm font-normal">
                    <Tag className="h-3 w-3" />
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">No tags</p>
            )}
            <div className="mt-6 pt-4 border-t border-border/50 space-y-2 text-xs text-muted-foreground font-mono">
              <div className="flex justify-between">
                <span>Created</span>
                <span>{new Date(trend.createdAt).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Updated</span>
                <span>{new Date(trend.updatedAt).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span>ID</span>
                <span>#{trend.id}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick status update */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader className="border-b border-border/50 bg-muted/20 pb-3 pt-4 px-5">
          <CardTitle className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Update Status</CardTitle>
        </CardHeader>
        <CardContent className="p-5">
          <div className="flex flex-wrap gap-2">
            {["emerging", "rising", "peaking", "declining"].map((s) => (
              <Button
                key={s}
                variant={trend.status === s ? "default" : "outline"}
                size="sm"
                className="capitalize"
                disabled={updateTrend.isPending}
                onClick={() => {
                  if (trend.status !== s) {
                    updateTrend.mutate({ id: trend.id, data: { status: s } });
                  }
                }}
              >
                {s}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
