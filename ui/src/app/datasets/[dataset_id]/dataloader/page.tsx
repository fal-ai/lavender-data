import Link from 'next/link';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { getClient } from '@/lib/api';
import { utcToLocal } from '@/lib/date';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent } from '@/components/ui/card';
import { Dataloader } from './dataloader';

export default async function DatasetDataloaderPage({
  params,
}: {
  params: Promise<{
    dataset_id: string;
  }>;
}) {
  const { dataset_id } = await params;
  const client = await getClient();
  const datasetResponse = await client.GET('/datasets/{dataset_id}', {
    params: { path: { dataset_id } },
  });

  if (datasetResponse.error) {
    return <ErrorCard error={datasetResponse.error.detail} />;
  }

  const filters = (await client.GET('/registries/filters')).data || [];
  const categorizers =
    (await client.GET('/registries/categorizers')).data || [];
  const collaters = (await client.GET('/registries/collaters')).data || [];
  const preprocessors =
    (await client.GET('/registries/preprocessors')).data || [];

  const shardsetOptions = datasetResponse.data.shardsets.map((shardset) => ({
    label: shardset.location,
    value: shardset.id as string,
    selected: false,
  }));

  return (
    <div className="flex flex-col gap-4">
      <Dataloader
        shardsetOptions={shardsetOptions}
        filters={filters}
        categorizers={categorizers}
        collaters={collaters}
        preprocessors={preprocessors}
      />
    </div>
  );
}
