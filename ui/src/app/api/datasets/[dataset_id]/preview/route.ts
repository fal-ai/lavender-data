import { type NextRequest } from 'next/server';
import { getClient } from '@/lib/api';

export async function GET(
  request: NextRequest,
  {
    params,
  }: {
    params: Promise<{ dataset_id: string }>;
  }
) {
  const { dataset_id } = await params;
  const searchParams = request.nextUrl.searchParams;
  const page = Number(searchParams.get('page')) || 0;
  const limit = Number(searchParams.get('limit')) || 20;

  if (!dataset_id) {
    return new Response(JSON.stringify({ error: 'Dataset ID is required' }), {
      status: 400,
    });
  }

  const client = await getClient();
  const response = await client.GET('/datasets/{dataset_id}/preview', {
    params: {
      path: { dataset_id },
      query: {
        offset: page * limit,
        limit: limit,
      },
    },
  });

  if (response.error) {
    return new Response(JSON.stringify(response.error), {
      status: response.response.status,
    });
  }

  return new Response(JSON.stringify(response.data));
}
