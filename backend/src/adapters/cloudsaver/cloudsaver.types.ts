import type { ResourceDto } from '../../types/resource';

export interface CloudSaverSearchLink {
  link: string;
  cloudType: string;
}

export interface CloudSaverSearchMessage {
  messageId: string;
  title: string;
  pubDate?: string;
  content?: string;
  image?: string;
  cloudLinks?: CloudSaverSearchLink[];
  tags?: string[];
  magnetLink?: string;
  channel?: string;
  channelId?: string;
}

export interface CloudSaverSearchChannel {
  id: string;
  index: number;
  list: CloudSaverSearchMessage[];
  channelInfo?: {
    id: string;
    name: string;
    index: number;
    channelLogo?: string;
  };
}

export interface CloudSaverSearchResponse {
  success: boolean;
  code: number;
  data: CloudSaverSearchChannel[];
  message: string;
}

export interface CloudSaverShareFileItem {
  fileId: string;
  fileName: string;
  fileSize: number;
  isFolder: boolean;
}

export interface CloudSaverShareInfoResponse {
  success: boolean;
  code: number;
  data: {
    list: CloudSaverShareFileItem[];
  };
  message: string;
}

export interface CloudSaverFolderItem {
  cid: string;
  name: string;
  path: Array<{
    name: string;
    cid?: string;
    pid?: string;
    aid?: string;
    isp?: string;
    p_cid?: string;
    iss?: string;
    fv?: string;
    fvs?: string;
  }>;
}

export interface CloudSaverFoldersResponse {
  success: boolean;
  code: number;
  data: CloudSaverFolderItem[];
  message: string;
}

export interface CloudSaverSaveResponse {
  success: boolean;
  code: number;
  data: unknown;
  message: string;
}

export interface CloudSaverTransferResult {
  success: boolean;
  message: string;
  data?: {
    savePath: string;
    fileCount: number;
    transferId: string;
    duplicate?: boolean;
  };
  raw?: unknown;
}

export interface CloudSaverSearchAdapter {
  search(keyword: string, driver: string): Promise<ResourceDto[]>;
}
