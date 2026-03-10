import { nanoid } from 'nanoid';
import { env } from '../../config/env';
import type { ResourceDto } from '../../types/resource';
import type {
  CloudSaverFolderItem,
  CloudSaverFoldersResponse,
  CloudSaverSaveResponse,
  CloudSaverShareFileItem,
  CloudSaverShareInfoResponse,
  CloudSaverTransferResult,
} from './cloudsaver.types';
import { CloudSaverClient } from './cloudsaver.client';
import { buildCloudSaverSavePath } from './cloudsaver.mapper';

function inferTargetFolderName(resource: ResourceDto): string {
  if (resource.mediaType === 'tv') {
    return env.CLOUDSAVER_DEFAULT_TV_FOLDER;
  }
  return env.CLOUDSAVER_DEFAULT_MOVIE_FOLDER;
}

function getShareParams(resource: ResourceDto): { shareCode: string; receiveCode: string } {
  const shareCode = String(resource.extra.shareCode ?? '');
  const receiveCode = String(resource.extra.receiveCode ?? '');
  if (!shareCode || !receiveCode) {
    throw new Error('资源缺少 115 shareCode 或 receiveCode');
  }
  return { shareCode, receiveCode };
}

function ensureSuccess(response: { success: boolean; message: string }): void {
  if (!response.success) {
    throw new Error(response.message || 'CloudSaver 调用失败');
  }
}

export class CloudSaverTransfer115Service {
  constructor(private readonly client: CloudSaverClient) {}

  private async fetchShareInfo(shareCode: string, receiveCode: string): Promise<CloudSaverShareFileItem[]> {
    const response = await this.client.get<CloudSaverShareInfoResponse>(env.CLOUDSAVER_115_SHARE_INFO_PATH, {
      shareCode,
      receiveCode,
    });
    ensureSuccess(response);
    return response.data.list;
  }

  private async fetchFolders(parentCid: string): Promise<CloudSaverFolderItem[]> {
    const response = await this.client.get<CloudSaverFoldersResponse>(env.CLOUDSAVER_115_FOLDERS_PATH, {
      parentCid,
    });
    ensureSuccess(response);
    return response.data;
  }

  async transfer(resource: ResourceDto): Promise<CloudSaverTransferResult> {
    if (env.CLOUDSAVER_MOCK) {
      return {
        success: true,
        message: 'Mock 115 transfer success',
        data: {
          savePath: `/115/${resource.title}`,
          fileCount: 1,
          transferId: nanoid(12),
        },
        raw: {
          mocked: true,
        },
      };
    }

    const { shareCode, receiveCode } = getShareParams(resource);
    const shareFiles = await this.fetchShareInfo(shareCode, receiveCode);
    if (shareFiles.length === 0) {
      return {
        success: false,
        message: '分享链接为空，未获取到可转存文件',
      };
    }

    const rootFolders = await this.fetchFolders('0');
    const folderName = inferTargetFolderName(resource);
    const targetFolder = rootFolders.find((folder) => folder.name === folderName);
    if (!targetFolder) {
      return {
        success: false,
        message: `未找到目标目录: ${folderName}`,
        raw: rootFolders,
      };
    }

    const primaryFile = shareFiles[0];
    const response = await this.client.post<CloudSaverSaveResponse>(env.CLOUDSAVER_115_SAVE_PATH, {
      shareCode,
      receiveCode,
      fileId: primaryFile.fileId,
      folderId: targetFolder.cid,
      fids: shareFiles.map((item) => item.fileId),
    });

    const duplicate = /无需重复接收|已接收/i.test(response.message);
    if (!response.success && !duplicate) {
      return {
        success: false,
        message: response.message || '115 转存失败',
        raw: response,
      };
    }

    return {
      success: true,
      message: duplicate ? '115 文件已存在，跳过重复接收' : '115 转存成功',
      data: {
        savePath: buildCloudSaverSavePath(targetFolder, primaryFile.fileName),
        fileCount: shareFiles.length,
        transferId: nanoid(12),
        duplicate,
      },
      raw: {
        saveResponse: response,
        targetFolder,
        shareFiles,
      },
    };
  }
}
