'use client';

import { useState, useEffect } from 'react';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { getBackgroundTasks } from '@/lib/client-side-api';
import { components } from '@/lib/api/v1';
import { utcToLocal } from '@/lib/date';

type TaskMetadata = components['schemas']['TaskMetadata'];

export default function BackgroundTasksPage() {
  const [loading, setLoading] = useState(true);
  const [backgroundTasks, setBackgroundTasks] = useState<TaskMetadata[]>([]);
  const [intervalRef, setIntervalRef] = useState<NodeJS.Timeout | null>(null);

  const refreshBackgroundTasks = async () => {
    const backgroundTasks = await getBackgroundTasks();
    setBackgroundTasks(backgroundTasks);
    setLoading(false);
  };

  useEffect(() => {
    refreshBackgroundTasks();
    setIntervalRef(setInterval(refreshBackgroundTasks, 1000));

    return () => {
      if (intervalRef != null) {
        clearInterval(intervalRef);
        setIntervalRef(null);
      }
    };
  }, []);

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
        {loading ? (
          <div className="text-center text-muted-foreground m-8">
            Loading...
          </div>
        ) : backgroundTasks.length > 0 ? (
          <Card className="w-full">
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead className="min-w-[200px]">Name</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Status</TableHead>
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
                      <TableCell>
                        {backgroundTask.status ? (
                          <div className="grid grid-cols-[120px_1fr] gap-2 items-center w-[300px]">
                            <Progress
                              className="w-full"
                              value={
                                backgroundTask.status.total > 0
                                  ? (100 * backgroundTask.status.current) /
                                    backgroundTask.status.total
                                  : 0
                              }
                            />
                            <div className="text-sm text-muted-foreground">
                              {backgroundTask.status.total > 0
                                ? `${backgroundTask.status.current} / ${backgroundTask.status.total} `
                                : ''}
                              {backgroundTask.status.status}
                            </div>
                          </div>
                        ) : (
                          'Unknown'
                        )}
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
