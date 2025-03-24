import createClient from 'openapi-fetch';
import type { paths } from './v1';

export const API_URL = process.env.NEXT_PUBLIC_API_URL;
export const client = createClient<paths>({
  baseUrl: API_URL,
});
