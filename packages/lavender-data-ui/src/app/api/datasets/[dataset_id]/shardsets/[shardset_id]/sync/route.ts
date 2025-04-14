import { type NextRequest } from 'next/server';
import { getClient } from '@/lib/api';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ dataset_id: string; shardset_id: string }> }
) {
  const { dataset_id, shardset_id } = await params;

  if (!dataset_id || !shardset_id) {
    return new Response(
      JSON.stringify({ error: 'Dataset ID and shardset ID are required' }),
      { status: 400 }
    );
  }

  const client = await getClient();
  const response = await client.GET(
    '/datasets/{dataset_id}/shardsets/{shardset_id}/sync',
    {
      params: {
        path: { dataset_id, shardset_id },
      },
    }
  );

  if (response.error) {
    return new Response(JSON.stringify(response.error), {
      status: response.response.status,
    });
  }

  return new Response(JSON.stringify(response.data));
}
