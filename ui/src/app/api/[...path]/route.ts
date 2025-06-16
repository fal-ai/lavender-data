import type { NextRequest } from 'next/server';
import { getClient } from '@/lib/api';

export async function GET(request: NextRequest) {
  const client = await getClient();
  const path = request.nextUrl.pathname.replace('/api', '');
  const response = await client.GET(path as any, {});

  return new Response(JSON.stringify(response.data), {
    status: response.response.status,
  });
}

export async function POST(request: NextRequest) {
  const client = await getClient();
  const path = request.nextUrl.pathname.replace('/api', '');

  let body = {};
  try {
    body = await request.json();
  } catch (e) {}
  const response = await client.POST(path as any, {
    body,
  });

  return new Response(JSON.stringify(response.data), {
    status: response.response.status,
  });
}
