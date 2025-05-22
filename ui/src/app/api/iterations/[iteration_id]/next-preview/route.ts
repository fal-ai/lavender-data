import { type NextRequest } from 'next/server';
import { getClient } from '@/lib/api';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ iteration_id: string }> }
) {
  const { iteration_id } = await params;

  if (!iteration_id) {
    return new Response(JSON.stringify({ error: 'Iteration ID is required' }), {
      status: 400,
    });
  }

  const client = await getClient();
  const response = await client.GET('/iterations/{iteration_id}/next-preview', {
    params: {
      path: {
        iteration_id,
      },
    },
  });

  if (!response.data) {
    return new Response(JSON.stringify(response.error), {
      status: response.response.status,
    });
  }

  return new Response(JSON.stringify(response.data));
}
