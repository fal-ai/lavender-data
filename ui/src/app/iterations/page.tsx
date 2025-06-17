import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import Link from 'next/link';
import { getClient } from '@/lib/api';
import { utcToLocal } from '@/lib/date';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { redirect } from 'next/navigation';
import { Search } from 'lucide-react';

export default async function IterationsPage({
  searchParams,
}: {
  searchParams: Promise<{
    dataset_id?: string;
  }>;
}) {
  const { dataset_id } = await searchParams;
  const datasetsResponse = await (await getClient()).GET('/datasets/');
  const iterationsResponse = await (
    await getClient()
  ).GET('/iterations/', {
    params: {
      query: { dataset_id: dataset_id || undefined },
    },
  });

  if (datasetsResponse.error) {
    return <ErrorCard error={datasetsResponse.error.detail} />;
  }

  const datasets = datasetsResponse.data;

  if (iterationsResponse.error) {
    return <ErrorCard error={iterationsResponse.error.detail} />;
  }

  const iterations = iterationsResponse.data;

  return (
    <div className="w-full flex flex-col gap-2">
      <div className="text-lg">Iterations</div>
      <Card className="w-full">
        <CardContent>
          <div className="w-full flex justify-start mb-4">
            <form
              className="flex gap-2"
              action={async (f: FormData) => {
                'use server';
                const datasetId = f.get('datasetId');
                redirect(
                  `/iterations?dataset_id=${datasetId !== 'all' ? datasetId : ''}`
                );
              }}
            >
              <Select defaultValue={dataset_id} name="datasetId">
                <SelectTrigger>
                  <SelectValue placeholder="Dataset" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all" className="text-muted-foreground">
                    All
                  </SelectItem>
                  {datasets.map((d) => (
                    <SelectItem key={d.id as string} value={d.id as string}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button type="submit" variant="outline">
                <Search />
              </Button>
            </form>
          </div>
          <Table className="w-full">
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Dataset</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Config</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {iterations.map((iteration: any) => (
                <TableRow key={iteration.id}>
                  <TableCell className="font-mono text-xs">
                    <Link href={`/iterations/${iteration.id}`}>
                      {iteration.id}
                    </Link>
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    <Link href={`/datasets/${iteration.dataset_id}`}>
                      {iteration.dataset_id}
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
