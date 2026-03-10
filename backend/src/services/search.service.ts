import type { MediaType, ResourceDto } from '../types/resource';
import { SearchHistoryRepository } from '../repositories/search-history.repository';
import { CloudSaverSearchService } from '../adapters/cloudsaver/cloudsaver.search';
import { PanSouSearchService } from '../adapters/pansou/pansou.search';

export class SearchService {
  constructor(
    private readonly cloudSaverSearchService: CloudSaverSearchService,
    private readonly panSouSearchService: PanSouSearchService,
    private readonly searchHistoryRepository: SearchHistoryRepository,
  ) {}

  async search(keyword: string, driver: string, mediaType: MediaType): Promise<ResourceDto[]> {
    const [cloudSaverResources, panSouResources] = await Promise.all([
      this.cloudSaverSearchService.search(keyword, driver, mediaType),
      this.panSouSearchService.search(keyword, mediaType),
    ]);

    const merged = new Map<string, ResourceDto>();
    [...cloudSaverResources, ...panSouResources].forEach((resource) => {
      const dedupeKey = `${String(resource.extra.shareCode ?? '')}:${String(resource.extra.receiveCode ?? '')}`;
      if (!merged.has(dedupeKey)) {
        merged.set(dedupeKey, resource);
      }
    });

    const resources = [...merged.values()];
    this.searchHistoryRepository.create({ keyword, driver, resultCount: resources.length });
    return resources;
  }
}
