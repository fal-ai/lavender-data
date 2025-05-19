import Link from 'next/link';
import { Columns, Eye, IterationCw, Plus, Settings } from 'lucide-react';
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
import { utcToLocal } from '@/lib/date';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent } from '@/components/ui/card';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb';
import { TabsContent } from '@/components/ui/tabs';
import { Tabs, TabsTrigger } from '@/components/ui/tabs';
import { TabsList } from '@/components/ui/tabs';
import { DeleteDatasetDialog } from './delete-dataset-dialog';
import { PreprocessDatasetDialog } from './preprocess-dataset-dialog';
import { DatasetPreview } from './dataset-preview';

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

export default async function DatasetDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{
    dataset_id: string;
  }>;
  searchParams: Promise<{
    tab: string;
  }>;
}) {
  const { dataset_id } = await params;
  const { tab = 'preview' } = await searchParams;
  const client = await getClient();
  const datasetResponse = await client.GET('/datasets/{dataset_id}', {
    params: { path: { dataset_id } },
  });
  const iterationsResponse = await client.GET('/iterations/', {
    params: { query: { dataset_id } },
  });
  const preprocessorsResponse = await client.GET(
    '/registries/preprocessors',
    {}
  );

  if (datasetResponse.error) {
    return <ErrorCard error={datasetResponse.error.detail} />;
  }

  if (iterationsResponse.error) {
    return <ErrorCard error={iterationsResponse.error.detail} />;
  }

  if (!preprocessorsResponse.data) {
    return <ErrorCard error={preprocessorsResponse.error} />;
  }

  const dataset = datasetResponse.data;
  const iterations = iterationsResponse.data;

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
    <main className="container flex w-full flex-1 flex-col items-center justify-center gap-8">
      <Breadcrumb className="w-full pt-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Home</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href="/datasets">Datasets</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{dataset.id}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="w-full flex flex-col gap-1">
        <div className="text-lg">{dataset.name}</div>
        <div className="text-xs text-muted-foreground">{dataset.id}</div>
      </div>

      <Tabs defaultValue={tab} className="w-full">
        <TabsList>
          <Link href={`/datasets/${dataset_id}?tab=preview`}>
            <TabsTrigger value="preview">
              <div className="flex items-center gap-1">
                <Eye className="w-4 h-4" />
                Preview
              </div>
            </TabsTrigger>
          </Link>
          <Link href={`/datasets/${dataset_id}?tab=shardsets`}>
            <TabsTrigger value="shardsets">
              <div className="flex items-center gap-1">
                <Columns className="w-4 h-4" />
                Shardsets
              </div>
            </TabsTrigger>
          </Link>
          <Link href={`/datasets/${dataset_id}?tab=iterations`}>
            <TabsTrigger value="iterations">
              <div className="flex items-center gap-1">
                <IterationCw className="w-4 h-4" />
                Iterations
              </div>
            </TabsTrigger>
          </Link>
          <Link href={`/datasets/${dataset_id}?tab=settings`}>
            <TabsTrigger value="settings">
              <div className="flex items-center gap-1">
                <Settings className="w-4 h-4" />
                Settings
              </div>
            </TabsTrigger>
          </Link>
        </TabsList>
        <TabsContent value="preview" className="flex flex-col gap-2">
          <DatasetPreview dataset_id={dataset_id} />
        </TabsContent>
        <TabsContent value="shardsets" className="flex flex-col gap-2">
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
                              (shardset: any) =>
                                shardset.id === column.shardset_id
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
        </TabsContent>
        <TabsContent value="iterations">
          <Card className="w-full">
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Config</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {iterations.map((iteration) => (
                    <TableRow key={iteration.id}>
                      <TableCell className="font-mono text-xs">
                        <Link href={`/iterations/${iteration.id}`}>
                          {iteration.id}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <div>{iteration.total}</div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {iteration.shuffle ? (
                          <>
                            <div>Shuffle seed: {iteration.shuffle_seed}</div>
                            <div>
                              Shuffle block size: {iteration.shuffle_block_size}
                            </div>
                          </>
                        ) : (
                          <div>No shuffle</div>
                        )}
                        {iteration.batch_size > 0 ? (
                          <div>Batch size: {iteration.batch_size}</div>
                        ) : (
                          <div>No batch</div>
                        )}
                        {iteration.replication_pg ? (
                          <div>
                            <div>
                              {iteration.replication_pg.length} pgs,{' '}
                              {iteration.replication_pg.reduce(
                                (acc: number, current: number[]) =>
                                  acc + current.length,
                                0
                              )}{' '}
                              ranks
                            </div>
                          </div>
                        ) : (
                          <div>No replication</div>
                        )}
                      </TableCell>
                      <TableCell>{utcToLocal(iteration.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent
          value="settings"
          className="w-full max-w-[720px] flex flex-col gap-2 items-start"
        >
          <Card className="w-full">
            <CardContent className="flex flex-col gap-2">
              <div className="grid grid-cols-[1fr_200px] gap-2">
                <div>
                  <div className="text-md">Preprocess</div>
                  <div className="text-xs text-muted-foreground">
                    Generate a new shardset by preprocessing the dataset.
                  </div>
                </div>
                <PreprocessDatasetDialog
                  datasetId={dataset_id}
                  shardsets={
                    dataset.shardsets as {
                      id: string;
                      location: string;
                    }[]
                  }
                  preprocessors={preprocessorsResponse.data}
                >
                  <Button variant="default">Preprocess</Button>
                </PreprocessDatasetDialog>
              </div>
              <div className="grid grid-cols-[1fr_200px] gap-2">
                <div>
                  <div className="text-md">Delete this dataset</div>
                  <div className="text-xs text-muted-foreground">
                    This action is irreversible.
                  </div>
                </div>
                <DeleteDatasetDialog datasetId={dataset_id}>
                  <Button variant="destructive">Delete this dataset</Button>
                </DeleteDatasetDialog>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  );
}
