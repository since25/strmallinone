import type { Request, Response } from 'express';
import { z } from 'zod';
import { SearchService } from '../services/search.service';

const searchSchema = z.object({
  keyword: z.string().trim().min(1, 'keyword is required'),
  driver: z.literal('115').default('115'),
  mediaType: z.enum(['movie', 'tv']).default('movie'),
});

export class SearchController {
  constructor(private readonly searchService: SearchService) {}

  search = async (req: Request, res: Response): Promise<void> => {
    const parsed = searchSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ success: false, error: parsed.error.issues[0]?.message ?? 'invalid payload' });
      return;
    }

    try {
      const data = await this.searchService.search(parsed.data.keyword, parsed.data.driver, parsed.data.mediaType);
      res.json({ success: true, data });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'search failed',
      });
    }
  };
}
