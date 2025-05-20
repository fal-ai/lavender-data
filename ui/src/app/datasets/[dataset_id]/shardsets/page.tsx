import Link from 'next/link';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { getClient } from '@/lib/api';
import type { components } from '@/lib/api/v1';
import { AddShardsetDialog } from './add-shardset-dialog';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent } from '@/components/ui/card';
import { TabsContent } from '@/components/ui/tabs';

function ShardSetInfo({ shardset }: { shardset: any }) {
  if (!shardset) {
    return <div>-</div>;
  }

  return (
    <Link href={`/datasets/${shardset.dataset_id}/shardsets/${shardset.id}`}>
      <div className="font-mono text-xs">{shardset.id}</div>
      <div className="text-xs text-muted-foreground">{shardset.location}</div>
      <div className="text-xs text-muted-foreground">
        total {shardset.total_samples} samples, {shardset.shard_count} shards
      </div>
    </Link>
  );
}

export default async function DatasetShardsetsPage({
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

  const dataset = datasetResponse.data;

  const columnsWithRowSpan: (components['schemas']['DatasetColumnPublic'] & {
    rowSpan: number;
  })[] = dataset.columns
    .filter((column) => column.name !== dataset.uid_column_name)
    .map((column, index) => ({ ...column, rowSpan: 1 }))
    .sort(
      (a, b) =>
        a.shardset_id.localeCompare(b.shardset_id) ||
        a.name.localeCompare(b.name)
    );

  let lastShardsetRowIndex = 0;
  columnsWithRowSpan.forEach((column, index) => {
    if (
      column.shardset_id !==
      columnsWithRowSpan[lastShardsetRowIndex].shardset_id
    ) {
      lastShardsetRowIndex = index;
    } else {
      columnsWithRowSpan[index].rowSpan = 0;
      columnsWithRowSpan[lastShardsetRowIndex].rowSpan++;
    }
  });

  return (
    <div className="flex flex-col gap-2">
      <Card className="w-full">
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Shardset</TableHead>
                <TableHead className="w-[100px]">Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell>-</TableCell>
                <TableCell className="font-mono text-xs">
                  {dataset.uid_column_name}
                </TableCell>
                <TableCell>-</TableCell>
                <TableCell>Unique identifier for each sample</TableCell>
              </TableRow>
              {columnsWithRowSpan.map((column) => (
                <TableRow key={column.id}>
                  {column.rowSpan > 0 && (
                    <TableCell rowSpan={column.rowSpan}>
                      <ShardSetInfo
                        shardset={dataset.shardsets.find(
                          (shardset: any) => shardset.id === column.shardset_id
                        )}
                      />
                    </TableCell>
                  )}
                  <TableCell className="font-mono text-xs">
                    {column.name}
                  </TableCell>
                  <TableCell>{column.type}</TableCell>
                  <TableCell>{column.description}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <div className="w-full flex justify-end">
        <AddShardsetDialog datasetId={dataset_id}>
          <Button variant="outline">
            <Plus />
            Shardset
          </Button>
        </AddShardsetDialog>
      </div>
    </div>
  );
}
