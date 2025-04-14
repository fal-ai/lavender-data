import 'server-only';

import createClient from 'openapi-fetch';
import type { paths } from './v1';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const client = createClient<paths>({
  baseUrl: API_URL,
  fetch: (url) => {
    return fetch(url, { cache: 'no-store' });
  },
});

export const getClient = async () => {
  const cookieStore = await cookies();
  const apiKey = cookieStore.get('lavender-data-api-key')?.value;
  return createClient<paths>({
    baseUrl: API_URL,
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
  return createClient<paths>({
    baseUrl: API_URL,
    headers: {
      Authorization: `Basic ${apiKey}`,
    },
    fetch: async (input) => {
      return fetch(input, { cache: 'no-store' });
    },
  });
};
