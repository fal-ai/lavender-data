import { Pagination } from '@/components/pagination';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { getClient } from '@/lib/api';
import SamplesTable from '../samples-table';

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

  const preview_limit = 20;
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
        offset: currentPage * preview_limit,
        limit: preview_limit,
      },
    }
  );

  if (createPreviewResponse.error) {
    return <ErrorCard error={createPreviewResponse.error.detail} />;
  }

  const { preview_id } = createPreviewResponse.data;

  const getPreview = async (dataset_id: string, preview_id: string) => {
    while (true) {
      const preview = await client.GET(
        '/datasets/{dataset_id}/preview/{preview_id}',
        {
          params: {
            path: {
              dataset_id,
              preview_id,
            },
          },
          cache: 'no-cache',
        }
      );

      if (preview.response.status === 400) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        continue;
      }

      return preview;
    }
  };

  const previewResponse = await getPreview(dataset_id, preview_id);

  if (previewResponse.error) {
    return <ErrorCard error={previewResponse.error.detail} />;
  }

  const preview = previewResponse.data;

  const totalPages = Math.ceil(preview.total / preview_limit);
  const fetchedColumns = preview.columns.map((column) => column.name);

  return (
    <Card className="w-full">
      <CardContent className="w-full">
        <SamplesTable
          datasetId={dataset_id}
          samples={preview.samples}
          fetchedColumns={fetchedColumns}
        />
      </CardContent>
      <CardFooter className="w-full flex justify-center">
        <Pagination
          buttonCount={10}
          totalPages={totalPages}
          currentPage={currentPage}
          pageHref={`/datasets/${dataset_id}/preview?preview_page={page}`}
        />
      </CardFooter>
    </Card>
  );
}
