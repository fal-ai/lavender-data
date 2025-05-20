import { getClient } from '@/lib/api';
import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const file_url = request.nextUrl.searchParams.get('file_url');
  if (!file_url) {
    return new Response(JSON.stringify({ error: 'file_url is required' }), {
      status: 400,
    });
  }

  const client = await getClient();
  const response = await client.GET('/files/type', {
    params: {
      query: {
        file_url,
      },
    },
  });

  if (response.error) {
    return new Response(JSON.stringify(response.error), {
      status: response.response.status,
    });
  }

  return new Response(JSON.stringify(response.data), {
    status: 200,
    headers: response.response.headers,
  });
}
