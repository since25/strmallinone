import { env } from '../../config/env';

export class CloudSaverClient {
  private buildHeaders(extraHeaders?: Record<string, string>): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: 'application/json, text/plain, */*',
      ...extraHeaders,
    };

    if (env.CLOUDSAVER_AUTH_TOKEN) {
      headers.Authorization = env.CLOUDSAVER_AUTH_TOKEN.startsWith('Bearer ')
        ? env.CLOUDSAVER_AUTH_TOKEN
        : `Bearer ${env.CLOUDSAVER_AUTH_TOKEN}`;
    }
    if (env.CLOUDSAVER_COOKIE) {
      headers.Cookie = env.CLOUDSAVER_COOKIE.startsWith('MoviePilot=')
        ? env.CLOUDSAVER_COOKIE
        : `MoviePilot=${env.CLOUDSAVER_COOKIE}`;
    }
    if (env.CLOUDSAVER_USER_AGENT) {
      headers['User-Agent'] = env.CLOUDSAVER_USER_AGENT;
    }
    if (env.CLOUDSAVER_ORIGIN) {
      headers.Origin = env.CLOUDSAVER_ORIGIN;
    }

    return headers;
  }

  async get<T>(path: string, query?: Record<string, string | number | undefined>): Promise<T> {
    const url = new URL(path, env.CLOUDSAVER_BASE_URL);
    Object.entries(query ?? {}).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });

    const response = await fetch(url, {
      method: 'GET',
      headers: this.buildHeaders(),
    });

    if (!response.ok) {
      throw new Error(`CloudSaver request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  }

  async post<T>(path: string, body: Record<string, unknown>): Promise<T> {
    const response = await fetch(new URL(path, env.CLOUDSAVER_BASE_URL), {
      method: 'POST',
      headers: this.buildHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`CloudSaver request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  }
}
