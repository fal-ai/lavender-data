import { getClient } from '@/lib/api';
import { ErrorCard } from '@/components/error-card';
import { DatasetNavTabs } from './nav-tabs';

export default async function DatasetDetailPageLayout({
  params,
  children,
}: {
  params: Promise<{
    dataset_id: string;
  }>;
  children: React.ReactNode;
}) {
  const { dataset_id } = await params;

  const client = await getClient();
  const datasetResponse = await client.GET('/datasets/{dataset_id}', {
    params: { path: { dataset_id } },
  });

  if (datasetResponse.error) {
    return <ErrorCard error={datasetResponse.error.detail} />;
  }

  const dataset = datasetResponse.data;

  return (
    <div className="w-full flex flex-col gap-2">
      <div className="w-full flex flex-col gap-1 pb-4">
        <div className="text-lg">{dataset.name}</div>
        <div className="text-xs text-muted-foreground">{dataset.id}</div>
      </div>

      <div className="w-full flex flex-col gap-2">
        <DatasetNavTabs dataset_id={dataset_id} />
        <div className="w-full">{children}</div>
      </div>
    </div>
  );
}
