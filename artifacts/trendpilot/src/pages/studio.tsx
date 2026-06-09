import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Play,
  RefreshCw,
  Video,
  Mic,
  FileText,
  Tag,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Zap,
  ExternalLink,
  Download,
} from "lucide-react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

interface ContentPackage {
  title: string;
  script: string;
  youtube_description: string;
  youtube_tags: string[];
  audio_path: string;
  video_path: string;
  shorts: string[];
  generated_at?: string;
}

function fetchPreview(): Promise<ContentPackage> {
  return fetch(`${BASE}/api/content/preview`).then((r) => {
    if (!r.ok) throw new Error("No content generated yet.");
    return r.json();
  });
}

function triggerRun(): Promise<{ status: string }> {
  return fetch(`${BASE}/api/content/run`, { method: "POST" }).then((r) => r.json());
}

export function Studio() {
  const queryClient = useQueryClient();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [runStatus, setRunStatus] = useState<"idle" | "running" | "done" | "error">("idle");

  const { data, isLoading, isError } = useQuery<ContentPackage>({
    queryKey: ["content-preview"],
    queryFn: fetchPreview,
    retry: false,
  });

  const mutation = useMutation({
    mutationFn: triggerRun,
    onMutate: () => setRunStatus("running"),
    onSuccess: () => {
      setRunStatus("done");
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["content-preview"] });
        setRunStatus("idle");
      }, 90000);
    },
    onError: () => setRunStatus("error"),
  });

  return (
    <div className="flex-1 p-6 lg:p-8 space-y-8 overflow-y-auto">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Content Studio</h1>
          <p className="text-muted-foreground">Generate and preview your daily YouTube content package.</p>
        </div>

        <Button
          onClick={() => mutation.mutate()}
          disabled={runStatus === "running"}
          className="gap-2"
        >
          {runStatus === "running" ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating… (~90s)
            </>
          ) : runStatus === "done" ? (
            <>
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Done — refreshing…
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" />
              Generate New Video
            </>
          )}
        </Button>
      </div>

      {runStatus === "running" && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="p-4 flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="text-sm">
              Pipeline running: fetching trends → writing script → synthesising voice → encoding video…
            </span>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <LoadingSkeleton />
      ) : isError ? (
        <EmptyState onGenerate={() => mutation.mutate()} generating={runStatus === "running"} />
      ) : data ? (
        <ContentView data={data} videoRef={videoRef} />
      ) : null}
    </div>
  );
}

function ContentView({
  data,
  videoRef,
}: {
  data: ContentPackage;
  videoRef: React.RefObject<HTMLVideoElement>;
}) {
  const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
  const ts = data.generated_at ? encodeURIComponent(data.generated_at) : Date.now();
  const videoSrc = `${BASE}/api/content/video?t=${ts}`;
  const audioSrc = `${BASE}/api/content/audio?t=${ts}`;

  return (
    <div className="space-y-6">
      <Card className="border-border/50 bg-card/50 backdrop-blur overflow-hidden">
        <CardHeader className="border-b border-border/50 bg-muted/20 flex flex-row items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <Video className="h-5 w-5 text-primary" />
            <div>
              <CardTitle>Video Preview</CardTitle>
              <CardDescription className="mt-0.5 line-clamp-1">{data.title}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
              <a href={videoSrc} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3.5 w-3.5" />
                Watch in new tab
              </a>
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
              <a href={videoSrc} download="trendpilot-video.mp4">
                <Download className="h-3.5 w-3.5" />
                Download
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0 bg-black">
          <video
            ref={videoRef}
            src={videoSrc}
            controls
            className="w-full max-h-[480px] object-contain"
            preload="auto"
          />
        </CardContent>
      </Card>

      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader className="border-b border-border/50 bg-muted/20 flex flex-row items-center gap-2">
          <Mic className="h-5 w-5 text-primary" />
          <CardTitle>Audio Track</CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <audio src={audioSrc} controls className="w-full" preload="metadata" />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-border/50 bg-card/50 backdrop-blur">
          <CardHeader className="border-b border-border/50 bg-muted/20 flex flex-row items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <CardTitle>Script</CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{data.script}</p>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader className="border-b border-border/50 bg-muted/20 flex flex-row items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              <CardTitle className="text-base">YouTube Description</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{data.youtube_description}</p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader className="border-b border-border/50 bg-muted/20 flex flex-row items-center gap-2">
              <Tag className="h-4 w-4 text-primary" />
              <CardTitle className="text-base">Tags</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-2">
                {data.youtube_tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs font-mono">
                    {tag}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {data.shorts && data.shorts.length > 0 && (
            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader className="border-b border-border/50 bg-muted/20">
                <CardTitle className="text-base">Shorts</CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-1">
                {data.shorts.map((s) => (
                  <div key={s} className="text-xs font-mono text-muted-foreground bg-muted/30 rounded px-2 py-1">
                    {s}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onGenerate, generating }: { onGenerate: () => void; generating: boolean }) {
  return (
    <Card className="border-dashed border-border/70 bg-card/30">
      <CardContent className="p-12 flex flex-col items-center justify-center gap-4 text-center">
        <div className="p-4 rounded-full bg-muted/30">
          <Video className="h-8 w-8 text-muted-foreground" />
        </div>
        <div>
          <p className="font-semibold text-foreground">No content generated yet</p>
          <p className="text-sm text-muted-foreground mt-1">
            Click Generate to run the full pipeline: trends → script → voice → video.
          </p>
        </div>
        <Button onClick={onGenerate} disabled={generating} className="gap-2 mt-2">
          {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
          {generating ? "Generating…" : "Generate Now"}
        </Button>
      </CardContent>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-[320px] w-full rounded-xl" />
      <Skeleton className="h-16 w-full rounded-xl" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="lg:col-span-2 h-64 rounded-xl" />
        <div className="space-y-4">
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-24 rounded-xl" />
        </div>
      </div>
    </div>
  );
}
