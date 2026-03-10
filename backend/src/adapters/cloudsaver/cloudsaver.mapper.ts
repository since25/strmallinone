import { nanoid } from 'nanoid';
import type { MediaType, ResourceDto } from '../../types/resource';
import type { CloudSaverFolderItem, CloudSaverSearchMessage } from './cloudsaver.types';

function decodeHtml(text: string): string {
  return text
    .replace(/<mark[^>]*>/g, '')
    .replace(/<\/mark>/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&#/g, '#')
    .replace(/\s+/g, ' ')
    .trim();
}

function parse115Link(link: string): { shareCode: string; receiveCode: string } | null {
  try {
    const normalized = decodeURIComponent(link.replace(/&amp;/g, '&').replace(/\s+/g, ''));
    const url = new URL(normalized);
    const match = url.pathname.match(/\/s\/([^/]+)/);
    const receiveCode =
      url.searchParams.get('password') ??
      normalized.match(/访问码[:：]([A-Za-z0-9]+)/)?.[1] ??
      url.hash.match(/访问码[:：]([A-Za-z0-9]+)/)?.[1] ??
      '';
    if (!match || !receiveCode) {
      return null;
    }

    return {
      shareCode: match[1],
      receiveCode,
    };
  } catch {
    return null;
  }
}

function inferSize(message: CloudSaverSearchMessage): string {
  const source = `${message.title} ${message.content ?? ''}`;
  const match = source.match(/(\d+(?:\.\d+)?\s?(?:GB|TB|MB|G|M))/i);
  return match?.[1] ?? '-';
}

export function mapCloudSaverSearchMessage(message: CloudSaverSearchMessage, mediaType: MediaType): ResourceDto | null {
  const link = message.cloudLinks?.find((item) => item.cloudType === 'pan115');
  if (!link) {
    return null;
  }

  const parsed = parse115Link(link.link);
  if (!parsed) {
    return null;
  }

  return {
    id: message.messageId || nanoid(10),
    title: decodeHtml(message.title || '未命名资源'),
    provider: '115',
    mediaType,
    rawType: mediaType,
    size: inferSize(message),
    shareUrl: link.link.replace(/&amp;/g, '&'),
    extra: {
      source: 'cloudsaver',
      shareCode: parsed.shareCode,
      receiveCode: parsed.receiveCode,
      channelId: message.channelId,
      channel: message.channel,
      content: message.content,
      image: message.image,
      tags: message.tags ?? [],
      raw: message,
    },
  };
}

export function buildCloudSaverSavePath(folder: CloudSaverFolderItem, fileName?: string): string {
  const folderPath = [...folder.path.map((item) => item.name).filter((name) => name !== '根目录'), folder.name].join('/');
  return fileName ? `${folderPath}/${fileName}` : folderPath;
}
