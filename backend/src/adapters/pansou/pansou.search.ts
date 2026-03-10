import type { MediaType, ResourceDto } from '../../types/resource';
import { env } from '../../config/env';
import { PanSouClient } from './pansou.client';
import { mapPanSouSearchItem } from './pansou.mapper';
import type { PanSouSearchResponse } from './pansou.types';

export class PanSouSearchService {
  constructor(private readonly client: PanSouClient) {}

  async search(keyword: string, mediaType: MediaType): Promise<ResourceDto[]> {
    if (!env.PANSOU_ENABLED) {
      return [];
    }

    const response = await this.client.post<PanSouSearchResponse>(env.PANSOU_SEARCH_PATH, {
      kw: keyword,
      cloud_types: ['115'],
    });

    const items = response.data.merged_by_type['115'] ?? [];
    return items
      .map((item) => mapPanSouSearchItem(item, mediaType))
      .filter((item): item is ResourceDto => item !== null);
  }
}
