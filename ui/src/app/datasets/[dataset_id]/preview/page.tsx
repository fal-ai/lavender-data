import { ErrorCard } from '@/components/error-card';
import { getClient } from '@/lib/api';
import { PreviewTable } from './preview-table';

export default async function DatasetPreviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ dataset_id: string }>;
  searchParams: Promise<{ preview_page: string }>;
}) {
  const { dataset_id } = await params;
  const { preview_page } = await searchParams;
  const client = await getClient();

  const limit = 20;
  const currentPage = Number(preview_page || 0);

  const createPreviewResponse = await client.POST(
    '/datasets/{dataset_id}/preview',
    {
      params: {
        path: {
          dataset_id,
        },
      },
      body: {
        offset: currentPage * limit,
        limit: limit,
      },
    }
  );

  if (createPreviewResponse.error) {
    return <ErrorCard error={createPreviewResponse.error.detail} />;
  }

  const { preview_id } = createPreviewResponse.data;

  return (
    <PreviewTable
      datasetId={dataset_id}
      previewId={preview_id}
      page={currentPage}
      limit={limit}
    />
  );
}
