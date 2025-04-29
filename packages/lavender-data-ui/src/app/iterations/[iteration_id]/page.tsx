import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { getClient } from '@/lib/api';
import {
  CircleCheck,
  CircleEllipsis,
  CircleSlash,
  CircleX,
} from 'lucide-react';
import { IconTooltip } from '@/components/icon-tooltip';
import { ErrorCard } from '@/components/error-card';
import { Button } from '@/components/ui/button';
import { revalidatePath } from 'next/cache';
import { Card, CardContent } from '@/components/ui/card';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

async function pushbackInprogressIndices(formData: FormData) {
  'use server';

  const iteration_id = formData.get('iteration_id') as string;

  await (
    await getClient()
  ).POST('/iterations/{iteration_id}/pushback', {
    params: { path: { iteration_id } },
  });

  revalidatePath(`/iterations/${iteration_id}`);
}

export default async function IterationDetailPage({
  params,
}: {
  params: Promise<{ iteration_id: string }>;
}) {
  const { iteration_id } = await params;
  const client = await getClient();
  const iterationResponse = await client.GET('/iterations/{iteration_id}', {
    params: { path: { iteration_id } },
  });

  const progressResponse = await client.GET(
    '/iterations/{iteration_id}/progress',
    {
      params: { path: { iteration_id } },
    }
  );

  if (iterationResponse.error) {
    return <ErrorCard error={iterationResponse.error.detail} />;
  }

  if (progressResponse.error) {
    return <ErrorCard error={progressResponse.error.detail} />;
  }

  const iteration = iterationResponse.data;
  const progress = progressResponse.data;

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center gap-8">
      <Breadcrumb className="w-full pt-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Home</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href="/iterations">Iterations</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{iteration.id}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="w-full flex flex-col gap-1">
        <div className="text-lg">{iteration.id}</div>
        <div className="text-xs text-muted-foreground">
          {iteration.dataset_id}
        </div>
      </div>
      <Card className="w-full">
        <CardContent className="w-full flex flex-col gap-2">
          <div className="w-full grid grid-cols-4 gap-2 items-center">
            <div className="text-sm text-muted-foreground col-span-1">
              <div className="text-sm text-muted-foreground col-span-1 flex flex-row gap-2 items-center">
                <IconTooltip
                  icon={<CircleEllipsis className="w-4 h-4" />}
                  content={<p>Current</p>}
                />
                {progress.current} / {progress.total} (
                {((progress.current / progress.total) * 100).toFixed(2)}
                %)
              </div>
            </div>
            <Progress
              value={(progress.current * 100) / progress.total}
              className="col-span-3"
            />
          </div>
          <div className="w-full grid grid-cols-4 gap-2 items-center">
            <div className="text-sm text-muted-foreground col-span-1 flex flex-row gap-2 items-center">
              <IconTooltip
                icon={<CircleCheck className="w-4 h-4" />}
                content={<p>Completed</p>}
              />
              {progress.completed} / {progress.total} (
              {((progress.completed / progress.total) * 100).toFixed(2)}%)
            </div>
            <Progress
              value={(progress.completed * 100) / progress.total}
              className="col-span-3"
            />
          </div>
          <div className="w-full grid grid-cols-4 gap-2 items-center">
            <div className="text-sm text-muted-foreground col-span-1">
              <div className="text-sm text-muted-foreground col-span-1 flex flex-row gap-2 items-center">
                <IconTooltip
                  icon={<CircleSlash className="w-4 h-4" />}
                  content={<p>Filtered</p>}
                />
                {progress.filtered} / {progress.total} (
                {((progress.filtered / progress.total) * 100).toFixed(2)}%)
              </div>
            </div>
            <Progress
              value={(progress.filtered * 100) / progress.total}
              className="col-span-3"
            />
          </div>
          <div className="w-full grid grid-cols-4 gap-2 items-center">
            <div className="text-sm text-muted-foreground col-span-1">
              <div className="text-sm text-muted-foreground col-span-1 flex flex-row gap-2 items-center">
                <IconTooltip
                  icon={<CircleX className="w-4 h-4" />}
                  content={<p>Failed</p>}
                />
                {progress.failed} / {progress.total} (
                {((progress.failed / progress.total) * 100).toFixed(2)}%)
              </div>
            </div>
            <Progress
              value={(progress.failed * 100) / progress.total}
              className="col-span-3"
            />
          </div>
        </CardContent>
      </Card>
      {progress.inprogress.length > 0 ? (
        <div className="w-full flex flex-col gap-2">
          <div className="text-lg">Indices in progress</div>
          <Card className="w-full">
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">Index</TableHead>
                    <TableHead>Rank</TableHead>
                    <TableHead>Started</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {progress.inprogress.map(({ index, rank, started_at }) => (
                    <TableRow key={started_at}>
                      <TableCell>{index}</TableCell>
                      <TableCell>{rank}</TableCell>
                      <TableCell>
                        {new Date(started_at * 1000).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
          <div className="w-full flex justify-end">
            <form action={pushbackInprogressIndices}>
              <input type="hidden" name="iteration_id" value={iteration_id} />
              <Button variant="outline" type="submit">
                Pushback
              </Button>
            </form>
          </div>
        </div>
      ) : (
        <div className="w-full flex flex-col gap-2">
          <div className="text-lg">No indices in progress</div>
        </div>
      )}
    </main>
  );
}
