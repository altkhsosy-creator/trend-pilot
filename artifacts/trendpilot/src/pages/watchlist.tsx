import {
  useListWatchlist,
  useRemoveFromWatchlist,
  useUpdateTrend,
  getListWatchlistQueryKey,
  getListTrendsQueryKey,
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendStatusBadge } from "@/components/trend-status-badge";
import { Link } from "wouter";
import { cn } from "@/lib/utils";
import { ArrowUpRight, ArrowDownRight, Eye, Trash2, Bell, BellOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function Watchlist() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: items, isLoading } = useListWatchlist({
    query: { queryKey: getListWatchlistQueryKey() },
  });

  const remove = useRemoveFromWatchlist({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getListWatchlistQueryKey() });
        toast({ title: "Removed from watchlist" });
      },
    },
  });

  const updateTrend = useUpdateTrend({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getListWatchlistQueryKey() });
        queryClient.invalidateQueries({ queryKey: getListTrendsQueryKey() });
      },
    },
  });

  return (
    <div className="flex-1 p-6 lg:p-8 space-y-6 overflow-y-auto">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Watchlist</h1>
        <p className="text-muted-foreground">Signals you're actively monitoring.</p>
      </div>

      {isLoading ? (
        <div className="grid gap-4">
          {Array(4).fill(0).map((_, i) => (
            <Card key={i} className="border-border/50 bg-card/50">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-48" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  <Skeleton className="h-8 w-20" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : items?.length === 0 ? (
        <Card className="border-border/50 bg-card/50 backdrop-blur">
          <CardContent className="py-20 text-center space-y-3">
            <Eye className="h-10 w-10 text-muted-foreground/40 mx-auto" />
            <div>
              <div className="font-medium text-foreground">No signals tracked yet</div>
              <div className="text-muted-foreground text-sm mt-1">
                Go to <Link href="/trends" className="text-primary underline underline-offset-2">Trends</Link> and click the eye icon to start watching a signal.
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {items?.map((item) => {
            const trend = item.trend;
            if (!trend) return null;
            return (
              <Card key={item.id} className="border-border/50 bg-card/50 backdrop-blur hover:bg-card/80 transition-colors">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0 space-y-2">
                      <div className="flex items-center gap-3 flex-wrap">
                        <Link href={`/trends/${trend.id}`} className="font-semibold text-lg text-foreground hover:text-primary transition-colors truncate">
                          {trend.name}
                        </Link>
                        <TrendStatusBadge status={trend.status} />
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="font-mono uppercase tracking-wider text-xs">{trend.category}</span>
                        <span className="font-mono">Score: <span className="text-foreground">{trend.score.toFixed(1)}</span></span>
                        <span className={cn(
                          "font-mono flex items-center gap-0.5",
                          trend.velocity > 0 ? "text-emerald-500" : trend.velocity < 0 ? "text-rose-500" : "text-muted-foreground"
                        )}>
                          {trend.velocity > 0 ? <ArrowUpRight className="h-3 w-3" /> : trend.velocity < 0 ? <ArrowDownRight className="h-3 w-3" /> : null}
                          {trend.velocity > 0 ? "+" : ""}{trend.velocity.toFixed(1)}%
                        </span>
                      </div>
                      {trend.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {trend.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs font-normal px-2">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                      {item.notes && (
                        <p className="text-sm text-muted-foreground bg-muted/40 rounded-md px-3 py-2 italic">
                          {item.notes}
                        </p>
                      )}
                      <div className="text-xs text-muted-foreground font-mono">
                        Watching since {new Date(item.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-3">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => remove.mutate({ id: item.id })}
                        title="Remove from watchlist"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        {item.alertEnabled ? <Bell className="h-3 w-3 text-primary" /> : <BellOff className="h-3 w-3" />}
                        <span className="hidden sm:inline">Alerts</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {items && items.length > 0 && (
        <Card className="border-border/50 bg-muted/20">
          <CardContent className="p-4 text-sm text-muted-foreground font-mono text-center">
            Monitoring {items.length} signal{items.length !== 1 ? "s" : ""} — Last refreshed: {new Date().toLocaleTimeString()}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
