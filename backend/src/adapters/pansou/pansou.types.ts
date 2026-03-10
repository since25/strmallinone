import type { ResourceDto } from '../../types/resource';

export interface PanSouSearchItem {
  url: string;
  password?: string;
  note: string;
  datetime?: string;
  source?: string;
  images?: string[];
}

export interface PanSouSearchResponse {
  code: number;
  message: string;
  data: {
    total: number;
    merged_by_type: Record<string, PanSouSearchItem[]>;
  };
}

export interface PanSouSearchAdapter {
  search(keyword: string): Promise<ResourceDto[]>;
}
