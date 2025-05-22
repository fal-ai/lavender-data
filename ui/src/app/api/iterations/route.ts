import { type NextRequest } from 'next/server';
import { getClient } from '@/lib/api';

export async function POST(request: NextRequest) {
  const client = await getClient();
  const body = await request.json();

  const response = await client.POST('/iterations/', {
    body: {
      ...body,
      batch_size: 0,
    },
  });

  if (!response.data) {
    return new Response(JSON.stringify(response.error), {
      status: response.response.status,
    });
  }

  return new Response(JSON.stringify(response.data));
}
