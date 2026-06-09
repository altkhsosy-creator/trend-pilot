import { useGetTrendsSummary, useGetTopTrends } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, Zap } from "lucide-react";
import { TrendStatusBadge } from "@/components/trend-status-badge";
import { Link } from "wouter";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function Dashboard() {
  const { data: summary, isLoading: loadingSummary } = useGetTrendsSummary();
  const { data: topTrends, isLoading: loadingTop } = useGetTopTrends({ limit: 5 });

  return (
    <div className="flex-1 p-6 lg:p-8 space-y-8 overflow-y-auto">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Market Intelligence</h1>
        <p className="text-muted-foreground">Real-time overview of the trending landscape.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card/50 backdrop-blur border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Total Signals</CardTitle>
            <Activity className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loadingSummary ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <div className="text-2xl font-bold font-mono tracking-tight">{summary?.total || 0}</div>
            )}
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Emerging</CardTitle>
            <Zap className="w-4 h-4 text-primary" />
          </CardHeader>
          <CardContent>
             {loadingSummary ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <div className="text-2xl font-bold font-mono tracking-tight text-primary">{summary?.emerging || 0}</div>
            )}
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Rising</CardTitle>
            <TrendingUp className="w-4 h-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
             {loadingSummary ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <div className="text-2xl font-bold font-mono tracking-tight text-emerald-500">{summary?.rising || 0}</div>
            )}
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur border-border/50 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">Declining</CardTitle>
            <TrendingDown className="w-4 h-4 text-rose-500" />
          </CardHeader>
          <CardContent>
             {loadingSummary ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <div className="text-2xl font-bold font-mono tracking-tight text-rose-500">{summary?.declining || 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 border-border/50 shadow-sm bg-card/50 backdrop-blur overflow-hidden flex flex-col">
          <CardHeader className="border-b border-border/50 bg-muted/20">
            <CardTitle>Top Momentum Signals</CardTitle>
            <CardDescription>Items with highest velocity score across all categories</CardDescription>
          </CardHeader>
          <div className="divide-y divide-border/50 flex-1 overflow-auto">
            {loadingTop ? (
              Array(5).fill(0).map((_, i) => (
                <div key={i} className="p-4 flex items-center justify-between">
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                  <Skeleton className="h-8 w-16" />
                </div>
              ))
            ) : topTrends?.length === 0 ? (
               <div className="p-8 text-center text-muted-foreground">No trends found.</div>
            ) : (
              topTrends?.map((trend) => (
                <Link key={trend.id} href={`/trends/${trend.id}`} className="block hover:bg-muted/30 transition-colors p-4 group">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-foreground group-hover:text-primary transition-colors">{trend.name}</div>
                      <div className="text-xs text-muted-foreground uppercase tracking-widest font-mono mt-1">{trend.category}</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <TrendStatusBadge status={trend.status} />
                      <div className={cn(
                        "font-mono text-sm flex items-center min-w-[4rem] justify-end",
                        trend.velocity > 0 ? "text-emerald-500" : trend.velocity < 0 ? "text-rose-500" : "text-muted-foreground"
                      )}>
                        {trend.velocity > 0 ? <ArrowUpRight className="w-3 h-3 mr-1" /> : trend.velocity < 0 ? <ArrowDownRight className="w-3 h-3 mr-1" /> : null}
                        {Math.abs(trend.velocity)}%
                      </div>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </Card>

        <Card className="border-border/50 shadow-sm bg-card/50 backdrop-blur overflow-hidden flex flex-col">
          <CardHeader className="border-b border-border/50 bg-muted/20">
            <CardTitle>Category Concentration</CardTitle>
            <CardDescription>Volume of signals by domain</CardDescription>
          </CardHeader>
          <CardContent className="p-0 flex-1 overflow-auto">
            {loadingSummary ? (
               <div className="p-4 space-y-4">
                {Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
               </div>
            ) : (
              <div className="divide-y divide-border/50">
                {summary?.byCategory?.map((cat) => (
                  <div key={cat.category} className="p-4 flex items-center justify-between">
                    <span className="font-medium text-sm text-muted-foreground uppercase tracking-wider">{cat.category}</span>
                    <span className="font-mono text-sm bg-secondary px-2 py-0.5 rounded text-secondary-foreground">{cat.count}</span>
                  </div>
                ))}
                {summary?.byCategory?.length === 0 && (
                   <div className="p-8 text-center text-muted-foreground">No data available.</div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
