import { pgTable, serial, text, real, timestamp, boolean, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";

export const trendsTable = pgTable("trends", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  category: text("category").notNull(),
  score: real("score").notNull(),
  velocity: real("velocity").notNull().default(0),
  status: text("status").notNull().default("emerging"),
  description: text("description"),
  source: text("source"),
  tags: jsonb("tags").$type<string[]>().notNull().default([]),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

export const insertTrendSchema = createInsertSchema(trendsTable).omit({ id: true, createdAt: true, updatedAt: true });
export type InsertTrend = z.infer<typeof insertTrendSchema>;
export type Trend = typeof trendsTable.$inferSelect;

export const watchlistTable = pgTable("watchlist", {
  id: serial("id").primaryKey(),
  trendId: serial("trend_id").notNull().references(() => trendsTable.id, { onDelete: "cascade" }),
  notes: text("notes"),
  alertEnabled: boolean("alert_enabled").notNull().default(false),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const insertWatchlistSchema = createInsertSchema(watchlistTable).omit({ id: true, createdAt: true });
export type InsertWatchlist = z.infer<typeof insertWatchlistSchema>;
export type WatchlistItem = typeof watchlistTable.$inferSelect;
