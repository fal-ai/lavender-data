import { ErrorCard } from '@/components/error-card';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Card, CardContent } from '@/components/ui/card';
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

export default async function BackgroundTasksPage() {
  const backgroundTasksResponse = await (
    await getClient()
  ).GET('/background-tasks/');

  if (!backgroundTasksResponse.data) {
    return <ErrorCard error={backgroundTasksResponse.error} />;
  }

  const backgroundTasks = backgroundTasksResponse.data;

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center gap-8">
      <Breadcrumb className="w-full pt-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Home</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>Background Tasks</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Background Tasks</div>
        {backgroundTasks.length > 0 ? (
          <Card className="w-full">
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead className="min-w-[200px]">Name</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backgroundTasks.map((backgroundTask) => (
                    <TableRow key={backgroundTask.uid}>
                      <TableCell className="font-mono text-xs">
                        {backgroundTask.uid}
                      </TableCell>
                      <TableCell>{backgroundTask.name}</TableCell>
                      <TableCell>
                        {utcToLocal(backgroundTask.start_time)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        ) : (
          <div className="text-center text-muted-foreground m-8">
            Nothing here yet.
          </div>
        )}
      </div>
    </main>
  );
}
