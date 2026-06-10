import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Play,
  Video,
  Mic,
  FileText,
  Tag,
  Loader2,
  CheckCircle2,
  Zap,
  ExternalLink,
  Download,
  Clock,
  HardDrive,
  Library,
  X,
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

interface ArchivedVideo {
  filename: string;
  size_mb: number;
  generated_at: string;
  title: string;
  script: string;
  youtube_description: string;
  youtube_tags: string[];
}

interface VideoLibrary {
  videos: ArchivedVideo[];
  total: number;
}

function fetchPreview(): Promise<ContentPackage> {
  return fetch(`${BASE}/api/content/preview`).then((r) => {
    if (!r.ok) throw new Error("No content generated yet.");
    return r.json();
  });
}

function fetchVideoLibrary(): Promise<VideoLibrary> {
  return fetch(`${BASE}/api/content/videos`).then((r) => {
    if (!r.ok) throw new Error("Could not load video library.");
    return r.json();
  });
}

function triggerRun(): Promise<{ status: string }> {
  return fetch(`${BASE}/api/content/run`, { method: "POST" }).then((r) => r.json());
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString("en-GB", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function Studio() {
  const queryClient = useQueryClient();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [runStatus, setRunStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [selectedVideo, setSelectedVideo] = useState<ArchivedVideo | null>(null);

  const { data, isLoading, isError } = useQuery<ContentPackage>({
    queryKey: ["content-preview"],
    queryFn: fetchPreview,
    retry: false,
  });

  const { data: library, refetch: refetchLibrary } = useQuery<VideoLibrary>({
    queryKey: ["video-library"],
    queryFn: fetchVideoLibrary,
    retry: false,
    refetchInterval: false,
  });

  const mutation = useMutation({
    mutationFn: triggerRun,
    onMutate: () => setRunStatus("running"),
    onSuccess: () => {
      setRunStatus("done");
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["content-preview"] });
        refetchLibrary();
        setRunStatus("idle");
      }, 90000);
    },
    onError: () => setRunStatus("error"),
  });

  return (
    <div className="flex-1 p-6 lg:p-8 space-y-8 overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Content Studio</h1>
          <p className="text-muted-foreground">Generate and compare your YouTube content videos.</p>
        </div>
        <Button onClick={() => mutation.mutate()} disabled={runStatus === "running"} className="gap-2">
          {runStatus === "running" ? (
            <><Loader2 className="h-4 w-4 animate-spin" />Generating… (~5 min)</>
          ) : runStatus === "done" ? (
            <><CheckCircle2 className="h-4 w-4 text-emerald-400" />Done — refreshing…</>
          ) : (
            <><Zap className="h-4 w-4" />Generate New Video</>
          )}
        </Button>
      </div>

      {/* Pipeline progress banner */}
      {runStatus === "running" && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="p-4 flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary shrink-0" />
            <span className="text-sm">
              Pipeline running: Reddit trends → script → emotion engine → voice (gTTS) → Pexels video → encoding…
            </span>
          </CardContent>
        </Card>
      )}

      {/* Latest video */}
      {isLoading ? (
        <LoadingSkeleton />
      ) : isError ? (
        <EmptyState onGenerate={() => mutation.mutate()} generating={runStatus === "running"} />
      ) : data ? (
        <ContentView data={data} videoRef={videoRef} />
      ) : null}

      {/* Video Library */}
      <VideoLibrarySection
        library={library}
        selectedVideo={selectedVideo}
        onSelect={setSelectedVideo}
        onClose={() => setSelectedVideo(null)}
      />
    </div>
  );
}

// -------------------------------------------------------
// Latest content view
// -------------------------------------------------------
function ContentView({
  data,
  videoRef,
}: {
  data: ContentPackage;
  videoRef: React.RefObject<HTMLVideoElement>;
}) {
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
              <CardTitle>Latest Video</CardTitle>
              <CardDescription className="mt-0.5 line-clamp-1">{data.title}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
              <a href={videoSrc} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3.5 w-3.5" />Watch in new tab
              </a>
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
              <a href={videoSrc} download="trendpilot-video.mp4">
                <Download className="h-3.5 w-3.5" />Download
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0 bg-black">
          <video ref={videoRef} src={videoSrc} controls className="w-full max-h-[480px] object-contain" preload="auto" />
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
                  <Badge key={tag} variant="secondary" className="text-xs font-mono">{tag}</Badge>
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
                  <div key={s} className="text-xs font-mono text-muted-foreground bg-muted/30 rounded px-2 py-1">{s}</div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------
// Video Library
// -------------------------------------------------------
function VideoLibrarySection({
  library,
  selectedVideo,
  onSelect,
  onClose,
}: {
  library: VideoLibrary | undefined;
  selectedVideo: ArchivedVideo | null;
  onSelect: (v: ArchivedVideo) => void;
  onClose: () => void;
}) {
  if (!library || library.total === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Library className="h-5 w-5 text-primary" />
        <h2 className="text-xl font-semibold">Video Library</h2>
        <Badge variant="secondary">{library.total} video{library.total !== 1 ? "s" : ""}</Badge>
      </div>

      {/* Selected video player */}
      {selectedVideo && (
        <Card className="border-primary/40 bg-card/60 backdrop-blur overflow-hidden">
          <CardHeader className="border-b border-border/50 bg-muted/20 flex flex-row items-center justify-between gap-2 flex-wrap py-3">
            <div className="flex items-center gap-2 min-w-0">
              <Play className="h-4 w-4 text-primary shrink-0" />
              <div className="min-w-0">
                <p className="font-medium text-sm truncate">{selectedVideo.title || selectedVideo.filename}</p>
                <p className="text-xs text-muted-foreground">{formatDate(selectedVideo.generated_at)}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
                <a href={`${BASE}/api/content/videos/${selectedVideo.filename}`} download={selectedVideo.filename}>
                  <Download className="h-3.5 w-3.5" />Download
                </a>
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0 bg-black">
            <video
              key={selectedVideo.filename}
              src={`${BASE}/api/content/videos/${selectedVideo.filename}`}
              controls
              autoPlay
              className="w-full max-h-[480px] object-contain"
              preload="auto"
            />
          </CardContent>
          {selectedVideo.script && (
            <CardContent className="p-4 border-t border-border/40 bg-muted/10">
              <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">Script</p>
              <p className="text-sm text-muted-foreground leading-relaxed line-clamp-4">{selectedVideo.script}</p>
            </CardContent>
          )}
        </Card>
      )}

      {/* Grid of all videos */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {library.videos.map((video) => (
          <VideoCard
            key={video.filename}
            video={video}
            isSelected={selectedVideo?.filename === video.filename}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}

function VideoCard({
  video,
  isSelected,
  onSelect,
}: {
  video: ArchivedVideo;
  isSelected: boolean;
  onSelect: (v: ArchivedVideo) => void;
}) {
  return (
    <Card
      className={`cursor-pointer transition-all hover:border-primary/60 hover:bg-card/80 overflow-hidden ${
        isSelected ? "border-primary bg-primary/5 ring-1 ring-primary/40" : "border-border/50 bg-card/40"
      }`}
      onClick={() => onSelect(video)}
    >
      {/* Thumbnail placeholder */}
      <div className="relative bg-black aspect-video flex items-center justify-center group">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/40" />
        <div className={`rounded-full p-3 transition-transform group-hover:scale-110 ${
          isSelected ? "bg-primary/90" : "bg-white/10 group-hover:bg-white/20"
        }`}>
          <Play className="h-5 w-5 text-white fill-white" />
        </div>
        <div className="absolute bottom-2 right-2 flex items-center gap-1 bg-black/60 rounded px-1.5 py-0.5">
          <HardDrive className="h-3 w-3 text-white/70" />
          <span className="text-white/80 text-xs">{video.size_mb} MB</span>
        </div>
      </div>

      <CardContent className="p-3 space-y-1.5">
        <p className="text-sm font-medium line-clamp-2 leading-snug">
          {video.title || video.filename}
        </p>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{formatDate(video.generated_at)}</span>
        </div>
        {video.youtube_tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {video.youtube_tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs px-1.5 py-0 h-4 font-normal">
                {tag}
              </Badge>
            ))}
            {video.youtube_tags.length > 3 && (
              <span className="text-xs text-muted-foreground">+{video.youtube_tags.length - 3}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// -------------------------------------------------------
// Empty / Loading states
// -------------------------------------------------------
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
