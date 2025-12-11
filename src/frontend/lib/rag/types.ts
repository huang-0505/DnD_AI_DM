import { z } from "zod"

export const DocumentChunkSchema = z.object({
  id: z.string(),
  content: z.string(),
  metadata: z.object({
    source: z.string(),
    page: z.number().optional(),
    section: z.string().optional(),
    type: z.enum(["rule", "lore", "monster", "spell", "item", "campaign"]),
    title: z.string().optional(),
  }),
  embedding: z.array(z.number()).optional(),
})

export type DocumentChunk = z.infer<typeof DocumentChunkSchema>

export const QueryResultSchema = z.object({
  chunk: DocumentChunkSchema,
  similarity: z.number(),
})

export type QueryResult = z.infer<typeof QueryResultSchema>
