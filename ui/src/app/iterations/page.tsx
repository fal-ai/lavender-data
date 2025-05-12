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
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
export default async function IterationsPage() {
  const iterationsResponse = await (await getClient()).GET('/iterations/');

  if (iterationsResponse.error) {
    return <ErrorCard error={iterationsResponse.error.detail} />;
  }

  const iterations = iterationsResponse.data;

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center gap-8">
      <Breadcrumb className="w-full pt-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Home</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Iterations</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Iterations</div>
        <Card className="w-full">
          <CardContent>
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
    </main>
  );
}
