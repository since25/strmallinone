import { env } from '../../config/env';

export class PanSouClient {
  async post<T>(path: string, body?: Record<string, unknown>): Promise<T> {
    const url = new URL(path, env.PANSOU_BASE_URL);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body ?? {}),
    });

    if (!response.ok) {
      throw new Error(`PanSou request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  }

  async get<T>(path: string, query?: Record<string, string | number | undefined>): Promise<T> {
    const url = new URL(path, env.PANSOU_BASE_URL);
    Object.entries(query ?? {}).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`PanSou request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  }
}
