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
import { Button } from '@/components/ui/button';
import { RefreshCcw } from 'lucide-react';
import { abortTask } from './abort-task-action';
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogTitle,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from '@/components/ui/alert-dialog';

type TaskMetadata = components['schemas']['TaskMetadata'];

export default function BackgroundTasksPage() {
  const [loading, setLoading] = useState(true);
  const [backgroundTasks, setBackgroundTasks] = useState<TaskMetadata[]>([]);

  const refreshBackgroundTasks = async () => {
    setLoading(true);
    const backgroundTasks = await getBackgroundTasks();
    setBackgroundTasks(backgroundTasks);
    setLoading(false);
  };

  useEffect(() => {
    refreshBackgroundTasks();
  }, []);

  const abortTaskAction = async (taskId: string) => {
    const response = await abortTask(taskId);
    if (response.success) {
      refreshBackgroundTasks();
    }
  };

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
        <div className="flex flex-row gap-2">
          <Button variant="outline" onClick={refreshBackgroundTasks}>
            <RefreshCcw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
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
                    <TableHead>Actions</TableHead>
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
                      <TableCell>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="destructive">Abort</Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This action cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() =>
                                  abortTaskAction(backgroundTask.uid)
                                }
                              >
                                Continue
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
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
