import { env } from '../../config/env';
import { CloudSaverAuthService } from './cloudsaver.auth';

export class CloudSaverClient {
  constructor(private readonly authService: CloudSaverAuthService) {}

  private async buildHeaders(extraHeaders?: Record<string, string>, forceRefresh = false): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      Accept: 'application/json, text/plain, */*',
      ...extraHeaders,
    };

    const authHeader = await this.authService.getAuthorizationHeader(forceRefresh);
    if (authHeader) {
      headers.Authorization = authHeader;
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

  private async request<T>(url: URL, init: RequestInit): Promise<T> {
    let response = await fetch(url, {
      ...init,
      headers: await this.buildHeaders(init.headers as Record<string, string> | undefined),
    });

    if (response.status === 401 && env.CLOUDSAVER_USERNAME && env.CLOUDSAVER_PASSWORD) {
      response = await fetch(url, {
        ...init,
        headers: await this.buildHeaders(init.headers as Record<string, string> | undefined, true),
      });
    }

    if (!response.ok) {
      throw new Error(`CloudSaver request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  }

  async get<T>(path: string, query?: Record<string, string | number | undefined>): Promise<T> {
    const url = new URL(path, env.CLOUDSAVER_BASE_URL);
    Object.entries(query ?? {}).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(path: string, body: Record<string, unknown>): Promise<T> {
    return this.request<T>(new URL(path, env.CLOUDSAVER_BASE_URL), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }
}
