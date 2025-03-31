import { type NextRequest } from 'next/server';
import { client } from '@/lib/api';

export async function GET(request: NextRequest) {
  const response = await client.GET('/version');

  return new Response(JSON.stringify(response.data));
}
