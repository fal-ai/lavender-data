import { getDirect } from '@/lib/api';
import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const path = request.nextUrl.pathname.replace('/api/files/', '');
  const response = await getDirect(`/files/${path}`);

  return response;
}
