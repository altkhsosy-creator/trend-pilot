import { Router } from "express";
import { db } from "@workspace/db";
import { trendsTable } from "@workspace/db";
import { eq, ilike, and, desc, sql } from "drizzle-orm";
import {
  ListTrendsQueryParams,
  CreateTrendBody,
  GetTrendParams,
  UpdateTrendParams,
  UpdateTrendBody,
  DeleteTrendParams,
  GetTopTrendsQueryParams,
} from "@workspace/api-zod";

const router = Router();

router.get("/trends/summary", async (req, res) => {
  const trends = await db.select().from(trendsTable);
  const total = trends.length;
  const rising = trends.filter((t) => t.status === "rising").length;
  const peaking = trends.filter((t) => t.status === "peaking").length;
  const declining = trends.filter((t) => t.status === "declining").length;
  const emerging = trends.filter((t) => t.status === "emerging").length;
  const avgScore = total > 0 ? trends.reduce((sum, t) => sum + t.score, 0) / total : 0;

  const categoryMap: Record<string, number> = {};
  for (const t of trends) {
    categoryMap[t.category] = (categoryMap[t.category] ?? 0) + 1;
  }
  const byCategory = Object.entries(categoryMap).map(([category, count]) => ({
    category,
    count,
  }));

  res.json({ total, rising, peaking, declining, emerging, byCategory, avgScore });
});

router.get("/trends/top", async (req, res) => {
  const parsed = GetTopTrendsQueryParams.safeParse(req.query);
  const limit = parsed.success && parsed.data.limit ? parsed.data.limit : 10;
  const trends = await db
    .select()
    .from(trendsTable)
    .orderBy(desc(trendsTable.score))
    .limit(limit);
  res.json(trends.map(formatTrend));
});

router.get("/trends", async (req, res) => {
  const parsed = ListTrendsQueryParams.safeParse(req.query);
  const params = parsed.success ? parsed.data : {};

  const conditions = [];
  if (params.category) {
    conditions.push(eq(trendsTable.category, params.category));
  }
  if (params.status) {
    conditions.push(eq(trendsTable.status, params.status));
  }
  if (params.search) {
    conditions.push(ilike(trendsTable.name, `%${params.search}%`));
  }

  const trends =
    conditions.length > 0
      ? await db.select().from(trendsTable).where(and(...conditions)).orderBy(desc(trendsTable.score))
      : await db.select().from(trendsTable).orderBy(desc(trendsTable.score));

  res.json(trends.map(formatTrend));
});

router.post("/trends", async (req, res) => {
  const parsed = CreateTrendBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid input", details: parsed.error.issues });
    return;
  }
  const { name, category, score, velocity, status, description, source, tags } = parsed.data;
  const [trend] = await db
    .insert(trendsTable)
    .values({
      name,
      category,
      score,
      velocity: velocity ?? 0,
      status: status ?? "emerging",
      description: description ?? null,
      source: source ?? null,
      tags: tags ?? [],
    })
    .returning();
  res.status(201).json(formatTrend(trend));
});

router.get("/trends/:id", async (req, res) => {
  const parsed = GetTrendParams.safeParse({ id: Number(req.params.id) });
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid id" });
    return;
  }
  const [trend] = await db.select().from(trendsTable).where(eq(trendsTable.id, parsed.data.id));
  if (!trend) {
    res.status(404).json({ error: "Trend not found" });
    return;
  }
  res.json(formatTrend(trend));
});

router.patch("/trends/:id", async (req, res) => {
  const parsedParams = UpdateTrendParams.safeParse({ id: Number(req.params.id) });
  if (!parsedParams.success) {
    res.status(400).json({ error: "Invalid id" });
    return;
  }
  const parsedBody = UpdateTrendBody.safeParse(req.body);
  if (!parsedBody.success) {
    res.status(400).json({ error: "Invalid input", details: parsedBody.error.issues });
    return;
  }
  const updates: Record<string, unknown> = { ...parsedBody.data, updatedAt: new Date() };
  const [updated] = await db
    .update(trendsTable)
    .set(updates)
    .where(eq(trendsTable.id, parsedParams.data.id))
    .returning();
  if (!updated) {
    res.status(404).json({ error: "Trend not found" });
    return;
  }
  res.json(formatTrend(updated));
});

router.delete("/trends/:id", async (req, res) => {
  const parsed = DeleteTrendParams.safeParse({ id: Number(req.params.id) });
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid id" });
    return;
  }
  await db.delete(trendsTable).where(eq(trendsTable.id, parsed.data.id));
  res.status(204).send();
});

function formatTrend(t: typeof trendsTable.$inferSelect) {
  return {
    ...t,
    tags: Array.isArray(t.tags) ? t.tags : [],
    createdAt: t.createdAt.toISOString(),
    updatedAt: t.updatedAt.toISOString(),
  };
}

export default router;
