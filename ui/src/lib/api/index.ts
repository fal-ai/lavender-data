import 'server-only';

import createClient from 'openapi-fetch';
import type { paths } from './v1';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export const getApiUrl = () => {
  return process.env.API_URL || 'http://localhost:8000';
};

export const getApiKey = async () => {
  const cookieStore = await cookies();
  const apiKey = cookieStore.get('lavender-data-api-key')?.value;
  return apiKey;
};

export const getDirect = async (path: string) => {
  const baseUrl = getApiUrl();
  const apiKey = await getApiKey();
  const url = new URL(path, baseUrl);
  return fetch(url, {
    headers: apiKey
      ? {
          Authorization: `Basic ${apiKey}`,
        }
      : {},
    cache: 'no-store',
  });
};

export const getClient = async () => {
  const baseUrl = getApiUrl();
  const apiKey = await getApiKey();
  return createClient<paths>({
    baseUrl,
    headers: apiKey
      ? {
          Authorization: `Basic ${apiKey}`,
        }
      : {},
    fetch: async (input) => {
      const response = await fetch(input, { cache: 'no-store' });
      if (response.status === 401 || response.status === 403) {
        redirect('/set-api-key');
      }
      return response;
    },
  });
};

export const getManualAuthClient = async (apiKey: string) => {
  const baseUrl = getApiUrl();
  return createClient<paths>({
    baseUrl,
    headers: {
      Authorization: `Basic ${apiKey}`,
    },
    fetch: async (input) => {
      return fetch(input, { cache: 'no-store' });
    },
  });
};
