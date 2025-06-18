import type { NextRequest } from 'next/server';
import { getClient } from '@/lib/api';

const refinePath = (path: string) => {
  let refinedPath = path.replace('/api', '');
  if (refinedPath == '/iterations') {
    refinedPath = '/iterations/';
  }
  return refinedPath;
};

export async function GET(request: NextRequest) {
  const client = await getClient();
  const path = refinePath(request.nextUrl.pathname);

  const query: Record<string, string> = {};
  for (const [key, value] of request.nextUrl.searchParams.entries()) {
    query[key] = value;
  }
  const response = await client.GET(path as any, {
    params: {
      query,
    },
  });

  return new Response(JSON.stringify(response.data ?? response.error), {
    status: response.response.status,
  });
}

export async function POST(request: NextRequest) {
  const client = await getClient();
  const path = refinePath(request.nextUrl.pathname);

  let body = {};
  try {
    body = await request.json();
  } catch (e) {}

  const response = await client.POST(path as any, {
    body,
  });

  return new Response(JSON.stringify(response.data ?? response.error), {
    status: response.response.status,
  });
}

export async function PUT(request: NextRequest) {
  const client = await getClient();
  const path = refinePath(request.nextUrl.pathname);

  let body = {};
  try {
    body = await request.json();
  } catch (e) {}

  const response = await client.POST(path as any, {
    body,
  });

  return new Response(JSON.stringify(response.data ?? response.error), {
    status: response.response.status,
  });
}
