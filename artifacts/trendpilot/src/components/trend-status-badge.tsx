import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function TrendStatusBadge({ status, className }: { status: string; className?: string }) {
  let colorClass = "";
  switch (status.toLowerCase()) {
    case "rising":
      colorClass = "bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 border-emerald-500/50";
      break;
    case "peaking":
      colorClass = "bg-amber-500/20 text-amber-500 hover:bg-amber-500/30 border-amber-500/50";
      break;
    case "declining":
      colorClass = "bg-rose-500/20 text-rose-500 hover:bg-rose-500/30 border-rose-500/50";
      break;
    case "emerging":
      colorClass = "bg-primary/20 text-primary hover:bg-primary/30 border-primary/50";
      break;
    default:
      colorClass = "bg-muted text-muted-foreground";
  }

  return (
    <Badge variant="outline" className={cn("uppercase tracking-wider font-mono text-[10px] whitespace-nowrap", colorClass, className)}>
      {status}
    </Badge>
  );
}
