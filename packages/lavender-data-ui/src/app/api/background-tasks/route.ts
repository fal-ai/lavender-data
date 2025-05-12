import { getClient } from '@/lib/api';

export async function GET() {
  const client = await getClient();
  const response = await client.GET('/background-tasks/');

  if (!response.data) {
    return new Response(JSON.stringify(response.error), {
      status: response.response.status,
    });
  }

  return new Response(JSON.stringify(response.data));
}
