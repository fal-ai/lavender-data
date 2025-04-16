import 'server-only';

import createClient from 'openapi-fetch';
import type { paths } from './v1';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export const getClient = async () => {
  const baseUrl = process.env.API_URL || 'http://localhost:8000';
  const cookieStore = await cookies();
  const apiKey = cookieStore.get('lavender-data-api-key')?.value;
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
  const baseUrl = process.env.API_URL || 'http://localhost:8000';
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
