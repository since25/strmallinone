import { CloudSaverClient } from './cloudsaver.client';
import { mapCloudSaverSearchMessage } from './cloudsaver.mapper';
import type { MediaType, ResourceDto } from '../../types/resource';
import type { CloudSaverSearchResponse } from './cloudsaver.types';
import { env } from '../../config/env';

const mockItems = (keyword: string) => [
  {
    messageId: `mock-${keyword}-1`,
    title: `${keyword} 4K Remux`,
    content: `${keyword} 电影资源`,
    cloudLinks: [{ link: 'https://115cdn.com/s/mock123?password=abcd', cloudType: 'pan115' }],
    tags: ['电影'],
    channel: 'mock',
    channelId: 'mock',
  },
  {
    messageId: `mock-${keyword}-2`,
    title: `${keyword} Season 1`,
    content: `${keyword} 全8集`,
    cloudLinks: [{ link: 'https://115cdn.com/s/mock456?password=efgh', cloudType: 'pan115' }],
    tags: ['电视剧'],
    channel: 'mock',
    channelId: 'mock',
  },
];

export class CloudSaverSearchService {
  constructor(private readonly client: CloudSaverClient) {}

  async search(keyword: string, _driver: string, mediaType: MediaType): Promise<ResourceDto[]> {
    if (env.CLOUDSAVER_MOCK) {
      return mockItems(keyword)
        .map((item) => mapCloudSaverSearchMessage(item, mediaType))
        .filter((item): item is ResourceDto => item !== null);
    }

    const response = await this.client.get<CloudSaverSearchResponse>(env.CLOUDSAVER_SEARCH_PATH, {
      keyword,
      lastMessageId: '',
    });

    return response.data
      .flatMap((channel) => channel.list)
      .map((item) => mapCloudSaverSearchMessage(item, mediaType))
      .filter((item): item is ResourceDto => item !== null);
  }
}
