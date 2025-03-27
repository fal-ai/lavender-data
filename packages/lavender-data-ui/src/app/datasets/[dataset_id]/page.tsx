import Link from 'next/link';
import { Plus, Ellipsis } from 'lucide-react';
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
import { client } from '@/lib/api';
import { AddShardsetDialog } from './add-shardset-dialog';
import { AddIterationDialog } from '@/app/iterations/add-iteration-dialog';
import { utcToLocal } from '@/lib/date';
import { ErrorCard } from '@/components/error-card';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

function ShardSetInfo({ shardset }: { shardset: any }) {
  if (!shardset) {
    return <div>-</div>;
  }

  return (
    <div>
      <Link href={`/datasets/${shardset.dataset_id}/shardsets/${shardset.id}`}>
        <div>{shardset.id}</div>
      </Link>
      <div className="text-xs text-muted-foreground">{shardset.location}</div>
      <div className="text-xs text-muted-foreground">
        total {shardset.total_samples} samples, {shardset.shard_count} shards
      </div>
    </div>
  );
}

async function DatasetPreview({
  dataset_id,
  preview_page,
}: {
  dataset_id: string;
  preview_page: number;
}) {
  const previewResponse = await client.GET('/datasets/{dataset_id}/preview', {
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
      <Table className="w-full">
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
                        <TooltipContent>{sanitizedValue}</TooltipContent>
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
      <div className="w-full flex justify-center">
        <Pagination
          centerButtonCount={5}
          totalPages={totalPages}
          currentPage={currentPage}
          pageHref={(page) => `/datasets/${dataset_id}?preview_page=${page}`}
        />
      </div>
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

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center space-y-8 py-10">
      <div className="w-full flex flex-col gap-1">
        <div className="text-lg">{dataset.name}</div>
        <div className="text-xs text-muted-foreground">{dataset.id}</div>
      </div>

      <DatasetPreview dataset_id={dataset_id} preview_page={preview_page} />

      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Columns</div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Shardset</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>{dataset.uid_column_name}</TableCell>
              <TableCell>-</TableCell>
              <TableCell>Unique identifier for each sample</TableCell>
              <TableCell>-</TableCell>
            </TableRow>
            {dataset.columns
              .filter((column) => column.name !== dataset.uid_column_name)
              .map((column) => (
                <TableRow key={column.id}>
                  <TableCell>{column.name}</TableCell>
                  <TableCell>{column.type}</TableCell>
                  <TableCell>{column.description}</TableCell>
                  <TableCell>
                    <ShardSetInfo
                      shardset={dataset.shardsets.find(
                        (shardset: any) => shardset.id === column.shardset_id
                      )}
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
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
        <Table className="w-full">
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
        <div className="w-full flex justify-end">
          <AddIterationDialog fixedDataset={dataset}>
            <Button variant="outline">
              <Plus />
              Iteration
            </Button>
          </AddIterationDialog>
        </div>
      </div>
    </main>
  );
}
