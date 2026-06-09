import { Router } from "express";
import { db } from "@workspace/db";
import { watchlistTable, trendsTable } from "@workspace/db";
import { eq } from "drizzle-orm";
import {
  AddToWatchlistBody,
  RemoveFromWatchlistParams,
} from "@workspace/api-zod";

const router = Router();

router.get("/watchlist", async (req, res) => {
  const rows = await db
    .select()
    .from(watchlistTable)
    .leftJoin(trendsTable, eq(watchlistTable.trendId, trendsTable.id));

  const items = rows.map((r) => ({
    id: r.watchlist.id,
    trendId: r.watchlist.trendId,
    notes: r.watchlist.notes,
    alertEnabled: r.watchlist.alertEnabled,
    createdAt: r.watchlist.createdAt.toISOString(),
    trend: r.trends
      ? {
          ...r.trends,
          tags: Array.isArray(r.trends.tags) ? r.trends.tags : [],
          createdAt: r.trends.createdAt.toISOString(),
          updatedAt: r.trends.updatedAt.toISOString(),
        }
      : null,
  }));

  res.json(items);
});

router.post("/watchlist", async (req, res) => {
  const parsed = AddToWatchlistBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid input", details: parsed.error.issues });
    return;
  }

  const { trendId, notes, alertEnabled } = parsed.data;

  const [trend] = await db.select().from(trendsTable).where(eq(trendsTable.id, trendId));
  if (!trend) {
    res.status(404).json({ error: "Trend not found" });
    return;
  }

  const [item] = await db
    .insert(watchlistTable)
    .values({
      trendId,
      notes: notes ?? null,
      alertEnabled: alertEnabled ?? false,
    })
    .returning();

  res.status(201).json({
    id: item.id,
    trendId: item.trendId,
    notes: item.notes,
    alertEnabled: item.alertEnabled,
    createdAt: item.createdAt.toISOString(),
    trend: {
      ...trend,
      tags: Array.isArray(trend.tags) ? trend.tags : [],
      createdAt: trend.createdAt.toISOString(),
      updatedAt: trend.updatedAt.toISOString(),
    },
  });
});

router.delete("/watchlist/:id", async (req, res) => {
  const parsed = RemoveFromWatchlistParams.safeParse({ id: Number(req.params.id) });
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid id" });
    return;
  }
  await db.delete(watchlistTable).where(eq(watchlistTable.id, parsed.data.id));
  res.status(204).send();
});

export default router;
