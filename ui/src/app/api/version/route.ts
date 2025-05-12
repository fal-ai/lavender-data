import { type NextRequest } from 'next/server';
import { getClient } from '@/lib/api';

export async function GET(request: NextRequest) {
  const client = await getClient();
  const response = await client.GET('/version');

  return new Response(JSON.stringify(response.data));
}
