import { useState } from "react";
import {
  useListTrends,
  useCreateTrend,
  useDeleteTrend,
  useAddToWatchlist,
  getListTrendsQueryKey,
  getGetTrendsSummaryQueryKey,
  getGetTopTrendsQueryKey,
  getListWatchlistQueryKey,
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TrendStatusBadge } from "@/components/trend-status-badge";
import { Link } from "wouter";
import { cn } from "@/lib/utils";
import {
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  Search,
  Eye,
  Trash2,
  Filter,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const CATEGORIES = ["Technology", "Marketing", "Health", "Finance", "Consumer", "Culture", "Science", "Politics"];
const STATUSES = ["emerging", "rising", "peaking", "declining"];

export function Trends() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [addOpen, setAddOpen] = useState(false);

  const params = {
    ...(search ? { search } : {}),
    ...(categoryFilter ? { category: categoryFilter } : {}),
    ...(statusFilter ? { status: statusFilter } : {}),
  };

  const { data: trends, isLoading } = useListTrends(params, {
    query: { queryKey: getListTrendsQueryKey(params) },
  });

  const createTrend = useCreateTrend({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getListTrendsQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetTrendsSummaryQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetTopTrendsQueryKey() });
        setAddOpen(false);
        toast({ title: "Trend added", description: "New signal is now being tracked." });
      },
    },
  });

  const deleteTrend = useDeleteTrend({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getListTrendsQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetTrendsSummaryQueryKey() });
        queryClient.invalidateQueries({ queryKey: getGetTopTrendsQueryKey() });
        toast({ title: "Trend removed" });
      },
    },
  });

  const addToWatchlist = useAddToWatchlist({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getListWatchlistQueryKey() });
        toast({ title: "Added to watchlist", description: "You'll be tracking this signal." });
      },
    },
  });

  function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    createTrend.mutate({
      data: {
        name: String(data.get("name")),
        category: String(data.get("category")),
        score: Number(data.get("score")),
        velocity: Number(data.get("velocity")),
        status: String(data.get("status")),
        description: String(data.get("description") || ""),
        source: String(data.get("source") || ""),
        tags: String(data.get("tags") || "")
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      },
    });
  }

  return (
    <div className="flex-1 p-6 lg:p-8 space-y-6 overflow-y-auto">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Trend Signals</h1>
          <p className="text-muted-foreground">Browse and manage all tracked signals.</p>
        </div>
        <Dialog open={addOpen} onOpenChange={setAddOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Add Trend
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Add New Trend Signal</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4 mt-2">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 space-y-1.5">
                  <Label htmlFor="name">Signal Name</Label>
                  <Input id="name" name="name" placeholder="e.g. Decentralized AI" required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="category">Category</Label>
                  <select
                    id="category"
                    name="category"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="status">Status</Label>
                  <select
                    id="status"
                    name="status"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="score">Score (0–100)</Label>
                  <Input id="score" name="score" type="number" min={0} max={100} step={0.1} placeholder="72.5" required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="velocity">Velocity (%)</Label>
                  <Input id="velocity" name="velocity" type="number" step={0.1} placeholder="+18.3" required />
                </div>
                <div className="col-span-2 space-y-1.5">
                  <Label htmlFor="description">Description</Label>
                  <Input id="description" name="description" placeholder="Brief description of this trend..." />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="source">Source</Label>
                  <Input id="source" name="source" placeholder="e.g. Google Trends" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="tags">Tags (comma-separated)</Label>
                  <Input id="tags" name="tags" placeholder="AI, automation, SaaS" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setAddOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={createTrend.isPending}>
                  {createTrend.isPending ? "Adding..." : "Add Signal"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search signals..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={categoryFilter || "__all__"} onValueChange={(v) => setCategoryFilter(v === "__all__" ? "" : v)}>
          <SelectTrigger className="w-40">
            <Filter className="h-3 w-3 mr-1 text-muted-foreground" />
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All Categories</SelectItem>
            {CATEGORIES.map((c) => (
              <SelectItem key={c} value={c}>{c}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter || "__all__"} onValueChange={(v) => setStatusFilter(v === "__all__" ? "" : v)}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All Statuses</SelectItem>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {(search || categoryFilter || statusFilter) && (
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            onClick={() => { setSearch(""); setCategoryFilter(""); setStatusFilter(""); }}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Trends Table */}
      <Card className="border-border/50 bg-card/50 backdrop-blur overflow-hidden">
        {isLoading ? (
          <div className="divide-y divide-border/50">
            {Array(8).fill(0).map((_, i) => (
              <div key={i} className="p-4 flex items-center gap-4">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-16 ml-auto" />
                <Skeleton className="h-5 w-16" />
              </div>
            ))}
          </div>
        ) : trends?.length === 0 ? (
          <div className="py-20 text-center space-y-2">
            <div className="text-muted-foreground text-sm">No signals match your filters.</div>
            <Button variant="ghost" size="sm" onClick={() => { setSearch(""); setCategoryFilter(""); setStatusFilter(""); }}>
              Clear filters
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            <div className="px-4 py-2 grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 text-xs font-mono text-muted-foreground uppercase tracking-widest">
              <span>Signal</span>
              <span className="w-28 text-center">Status</span>
              <span className="w-20 text-right">Score</span>
              <span className="w-20 text-right">Velocity</span>
              <span className="w-16"></span>
            </div>
            {trends?.map((trend) => (
              <div
                key={trend.id}
                className="px-4 py-3 grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 items-center hover:bg-muted/30 transition-colors group"
              >
                <div>
                  <Link href={`/trends/${trend.id}`} className="font-semibold text-foreground hover:text-primary transition-colors">
                    {trend.name}
                  </Link>
                  <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider mt-0.5">
                    {trend.category}
                    {trend.tags?.length > 0 && (
                      <span className="ml-2">
                        {trend.tags.slice(0, 2).map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-[9px] px-1 py-0 ml-1 font-normal">
                            {tag}
                          </Badge>
                        ))}
                      </span>
                    )}
                  </div>
                </div>
                <div className="w-28 flex justify-center">
                  <TrendStatusBadge status={trend.status} />
                </div>
                <div className="w-20 text-right font-mono text-sm">
                  {trend.score.toFixed(1)}
                </div>
                <div className={cn(
                  "w-20 text-right font-mono text-sm flex items-center justify-end gap-0.5",
                  trend.velocity > 0 ? "text-emerald-500" : trend.velocity < 0 ? "text-rose-500" : "text-muted-foreground"
                )}>
                  {trend.velocity > 0 ? <ArrowUpRight className="h-3 w-3" /> : trend.velocity < 0 ? <ArrowDownRight className="h-3 w-3" /> : null}
                  {trend.velocity > 0 ? "+" : ""}{trend.velocity.toFixed(1)}%
                </div>
                <div className="w-16 flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    title="Add to watchlist"
                    onClick={() => addToWatchlist.mutate({ data: { trendId: trend.id } })}
                  >
                    <Eye className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-destructive hover:text-destructive"
                    title="Delete"
                    onClick={() => deleteTrend.mutate({ id: trend.id })}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
