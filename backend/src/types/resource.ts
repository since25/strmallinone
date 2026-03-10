export type Provider = '115';
export type MediaType = 'movie' | 'tv';

export interface ResourceDto {
  id: string;
  title: string;
  provider: Provider;
  mediaType: MediaType;
  rawType: string;
  size: string;
  shareUrl: string;
  extra: Record<string, unknown>;
}
