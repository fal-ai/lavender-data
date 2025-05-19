import { getDirect } from '@/lib/api';
import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const file_url = request.nextUrl.searchParams.get('file_url');
  if (!file_url) {
    return new Response(JSON.stringify({ error: 'file_url is required' }), {
      status: 400,
    });
  }

  const response = await getDirect(`/files/?file_url=${file_url}`);

  return response;
}
