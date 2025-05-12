'use server';

import { Buffer } from 'buffer';
import { getManualAuthClient } from '@/lib/api';
import { cookies } from 'next/headers';

export const setApiKey = async (formData: FormData) => {
  const apiKey = formData.get('apiKey') as string;
  if (!apiKey) {
    return { error: 'API Key is required', redirect: null };
  }

  const basicAuth = Buffer.from(apiKey, 'binary').toString('base64');

  const response = await (
    await getManualAuthClient(basicAuth)
  ).GET('/datasets/');
  if (response.error && response.response.status === 401) {
    return { error: String(response.error.detail), redirect: null };
  }

  const cookieStore = await cookies();
  cookieStore.set('lavender-data-api-key', basicAuth);
  return { error: null, redirect: '/' };
};
