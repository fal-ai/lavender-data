'use client';

import { useEffect, useState } from 'react';
import { Pagination } from '@/components/pagination';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import SamplesTable from '../samples-table';
import { components } from '@/lib/api/v1';
import { getDatasetPreview } from '@/lib/client-side-api';
import { ErrorCard } from '@/components/error-card';
import Loading from '../loading';

const pollPreview = async (
  dataset_id: string,
  preview_id: string,
  timeout: number
) => {
  const start_time = Date.now();

  while (true) {
    try {
      return await getDatasetPreview(dataset_id, preview_id);
    } catch (error) {
      if (Date.now() - start_time > timeout) {
        throw new Error('Preview timed out');
      }
      if (!(error instanceof Error)) {
        throw error;
      }
      if (error.message.includes('400')) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        continue;
      } else {
        throw error;
      }
    }
  }
};

export function PreviewTable({
  datasetId,
  previewId,
  page,
  limit,
}: {
  datasetId: string;
  previewId: string;
  page: number;
  limit: number;
}) {
  const [preview, setPreview] = useState<
    components['schemas']['GetDatasetPreviewResponse'] | null
  >(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    pollPreview(datasetId, previewId, 60 * 1000)
      .then((preview) => {
        setPreview(preview);
      })
      .catch((error) => {
        setError(error.message);
      });
  }, [datasetId, previewId]);

  if (error) {
    return <ErrorCard error={error} />;
  }

  if (!preview) {
    return <Loading />;
  }

  return (
    <Card className="w-full">
      <CardContent className="w-full">
        <SamplesTable
          datasetId={datasetId}
          samples={preview.samples}
          fetchedColumns={preview.columns.map((column) => column.name)}
        />
      </CardContent>
      <CardFooter className="w-full flex justify-center">
        <Pagination
          buttonCount={10}
          totalPages={Math.ceil(preview.total / limit)}
          currentPage={page}
          pageHref={`/datasets/${datasetId}/preview?preview_page={page}`}
        />
      </CardFooter>
    </Card>
  );
}
