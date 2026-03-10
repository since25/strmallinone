import { nanoid } from 'nanoid';
import type { MediaType, ResourceDto } from '../../types/resource';
import type { PanSouSearchItem } from './pansou.types';

function decode115Link(link: string, password?: string): { shareCode: string; receiveCode: string } | null {
  try {
    const normalized = decodeURIComponent(link.replace(/&amp;/g, '&').replace(/\s+/g, ''));
    const url = new URL(normalized);
    const match = url.pathname.match(/\/s\/([^/]+)/);
    const receiveCode =
      password ||
      url.searchParams.get('password') ||
      normalized.match(/访问码[:：]([A-Za-z0-9]+)/)?.[1] ||
      url.hash.match(/访问码[:：]([A-Za-z0-9]+)/)?.[1] ||
      '';
    if (!match || !receiveCode) {
      return null;
    }

    return { shareCode: match[1], receiveCode };
  } catch {
    return null;
  }
}

export function mapPanSouSearchItem(item: PanSouSearchItem, mediaType: MediaType): ResourceDto | null {
  if (!/115/.test(item.url)) {
    return null;
  }

  const parsed = decode115Link(item.url, item.password);
  if (!parsed) {
    return null;
  }

  return {
    id: `pansou_${parsed.shareCode}_${parsed.receiveCode}` || nanoid(10),
    title: item.note || '未命名资源',
    provider: '115',
    mediaType,
    rawType: mediaType,
    size: '-',
    shareUrl: item.url,
    extra: {
      source: 'pansou',
      shareCode: parsed.shareCode,
      receiveCode: parsed.receiveCode,
      datetime: item.datetime,
      image: item.images?.[0],
      searchSource: item.source,
      raw: item,
    },
  };
}
