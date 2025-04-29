import Link from 'next/link';
import { Plus } from 'lucide-react';
import { isInteger } from 'lodash';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Pagination } from '@/components/pagination';
import { getClient } from '@/lib/api';
import type { components } from '@/lib/api/v1';
import { AddShardsetDialog } from './add-shardset-dialog';
import { utcToLocal } from '@/lib/date';
import { ErrorCard } from '@/components/error-card';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb';

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

async function DatasetPreview({
  dataset_id,
  preview_page,
}: {
  dataset_id: string;
  preview_page: number;
}) {
  const previewResponse = await (
    await getClient()
  ).GET('/datasets/{dataset_id}/preview', {
    params: {
      path: { dataset_id },
      query: {
        offset: Number(preview_page) * preview_limit,
        limit: preview_limit,
      },
    },
  });

  const preview = previewResponse.data;

  if (!preview) {
    return (
      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Preview</div>
        <ErrorCard error="Preview is not available for this dataset." />
      </div>
    );
  }

  const totalPages = Math.ceil(preview.total / preview_limit);
  const currentPage = Number(preview_page);

  return (
    <div className="w-full flex flex-col gap-2">
      <div className="text-lg">Preview</div>
      <Card className="w-full">
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                {preview.columns.map((column) => (
                  <TableHead key={column.id}>{column.name}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {preview.samples.map((sample, index) => (
                <TableRow key={`preview-sample-${index}`}>
                  {preview.columns.map((column) => {
                    const value = sample[column.name];
                    let sanitizedValue: string;
                    let ellipsizedValue: string | null = null;
                    if (typeof value === 'object' && value !== null) {
                      sanitizedValue = JSON.stringify(value);
                    } else if (typeof value === 'number') {
                      if (isInteger(value)) {
                        sanitizedValue = String(value);
                      } else {
                        sanitizedValue = (value as number).toFixed(8);
                        ellipsizedValue = (value as number).toFixed(2);
                      }
                    } else {
                      sanitizedValue = String(value);
                    }

                    if (sanitizedValue.length > 50) {
                      ellipsizedValue = sanitizedValue.slice(0, 50) + '...';
                    }
                    return (
                      <TableCell key={column.id}>
                        {ellipsizedValue ? (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div>{ellipsizedValue}</div>
                            </TooltipTrigger>
                            <TooltipContent className="w-auto max-w-[500px] text-wrap break-all">
                              {sanitizedValue}
                            </TooltipContent>
                          </Tooltip>
                        ) : (
                          <div>{sanitizedValue}</div>
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
        <CardFooter className="w-full flex justify-center">
          <Pagination
            centerButtonCount={5}
            totalPages={totalPages}
            currentPage={currentPage}
            pageHref={(page) => `/datasets/${dataset_id}?preview_page=${page}`}
          />
        </CardFooter>
      </Card>
    </div>
  );
}

const preview_limit = 10;

export default async function DatasetDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{
    dataset_id: string;
  }>;
  searchParams: Promise<{
    preview_page: number;
  }>;
}) {
  const { dataset_id } = await params;
  const { preview_page = 0 } = await searchParams;
  const client = await getClient();
  const datasetResponse = await client.GET('/datasets/{dataset_id}', {
    params: { path: { dataset_id } },
  });
  const iterationsResponse = await client.GET('/iterations/', {
    params: { query: { dataset_id } },
  });

  if (datasetResponse.error) {
    return <ErrorCard error={datasetResponse.error.detail} />;
  }

  if (iterationsResponse.error) {
    return <ErrorCard error={iterationsResponse.error.detail} />;
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

      <DatasetPreview dataset_id={dataset_id} preview_page={preview_page} />

      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Shardsets and Columns</div>
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
      </div>

      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Iterations</div>
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
      </div>
    </main>
  );
}
