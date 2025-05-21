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
import DataloaderCode from './dataloader-code';

export default async function DatasetIterationsPage({
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

  const iterationsResponse = await client.GET('/iterations/', {
    params: { query: { dataset_id } },
  });

  const filters = (await client.GET('/registries/filters')).data || [];
  const categorizers =
    (await client.GET('/registries/categorizers')).data || [];
  const collaters = (await client.GET('/registries/collaters')).data || [];
  const preprocessors =
    (await client.GET('/registries/preprocessors')).data || [];

  if (iterationsResponse.error) {
    return <ErrorCard error={iterationsResponse.error.detail} />;
  }

  const iterations = iterationsResponse.data;
  const shardsetOptions = datasetResponse.data.shardsets.map((shardset) => ({
    label: shardset.location,
    value: shardset.id as string,
    selected: false,
  }));

  return (
    <div className="flex flex-col gap-4">
      <DataloaderCode
        shardsetOptions={shardsetOptions}
        filters={filters}
        categorizers={categorizers}
        collaters={collaters}
        preprocessors={preprocessors}
      />
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
  );
}
