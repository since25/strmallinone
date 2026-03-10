import { env } from '../../config/env';
import type { CloudSaverLoginResponse } from './cloudsaver.types';

export class CloudSaverAuthService {
  private token: string | null = null;
  private loginPromise: Promise<string> | null = null;

  async getAuthorizationHeader(forceRefresh = false): Promise<string | undefined> {
    if (!forceRefresh && this.token) {
      return `Bearer ${this.token}`;
    }

    if (!env.CLOUDSAVER_USERNAME || !env.CLOUDSAVER_PASSWORD) {
      if (!env.CLOUDSAVER_AUTH_TOKEN) {
        return undefined;
      }
      return env.CLOUDSAVER_AUTH_TOKEN.startsWith('Bearer ')
        ? env.CLOUDSAVER_AUTH_TOKEN
        : `Bearer ${env.CLOUDSAVER_AUTH_TOKEN}`;
    }

    const token = await this.login(forceRefresh);
    return `Bearer ${token}`;
  }

  private async login(forceRefresh: boolean): Promise<string> {
    if (!forceRefresh && this.loginPromise) {
      return this.loginPromise;
    }

    this.loginPromise = this.performLogin();

    try {
      const token = await this.loginPromise;
      this.token = token;
      return token;
    } finally {
      this.loginPromise = null;
    }
  }

  private async performLogin(): Promise<string> {
    const response = await fetch(new URL(env.CLOUDSAVER_LOGIN_PATH, env.CLOUDSAVER_BASE_URL), {
      method: 'POST',
      headers: {
        Accept: 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        ...(env.CLOUDSAVER_USER_AGENT ? { 'User-Agent': env.CLOUDSAVER_USER_AGENT } : {}),
        ...(env.CLOUDSAVER_ORIGIN ? { Origin: env.CLOUDSAVER_ORIGIN } : {}),
      },
      body: JSON.stringify({
        username: env.CLOUDSAVER_USERNAME,
        password: env.CLOUDSAVER_PASSWORD,
      }),
    });

    if (!response.ok) {
      throw new Error(`CloudSaver login failed with status ${response.status}`);
    }

    const payload = (await response.json()) as CloudSaverLoginResponse;
    const token = payload.data?.token;
    if (!payload.success || !token) {
      throw new Error(payload.message || 'CloudSaver login returned no token');
    }

    return token;
  }
}
