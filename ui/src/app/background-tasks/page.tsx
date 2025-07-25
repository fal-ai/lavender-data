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
import { Switch } from '@/components/ui/switch';

type TaskItem = components['schemas']['TaskItem'];

export default function BackgroundTasksPage() {
  const [loading, setLoading] = useState(true);
  const [backgroundTasks, setBackgroundTasks] = useState<TaskItem[]>([]);
  const [refreshCount, setRefreshCount] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const refreshBackgroundTasks = async ({
    more = false,
  }: {
    more?: boolean;
  }) => {
    const backgroundTasks = await getBackgroundTasks();
    setBackgroundTasks(backgroundTasks);
    if (more) {
      setTimeout(() => {
        setRefreshCount((prev) => prev + 1);
      }, 1000);
    }
  };

  useEffect(() => {
    setLoading(true);
    refreshBackgroundTasks({ more: true });
    setLoading(false);
  }, []);

  useEffect(() => {
    refreshBackgroundTasks({ more: autoRefresh });
  }, [refreshCount, autoRefresh]);

  const abortTaskAction = async (taskId: string) => {
    const response = await abortTask(taskId);
    if (response.success && !autoRefresh) {
      setLoading(true);
      refreshBackgroundTasks({ more: false });
      setLoading(false);
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
        <div className="flex flex-row gap-2 items-center">
          <RefreshCcw className="w-4 h-4" />
          <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
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
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backgroundTasks.map((backgroundTask) => (
                    <TableRow key={backgroundTask.task_id}>
                      <TableCell className="font-mono text-xs">
                        {backgroundTask.task_id}
                      </TableCell>
                      <TableCell>
                        {backgroundTask.status ? (
                          <div className="grid grid-cols-[120px_1fr] gap-2 items-center w-[300px]">
                            <Progress
                              className="w-full"
                              value={
                                backgroundTask.total > 0
                                  ? (100 * backgroundTask.current) /
                                    backgroundTask.total
                                  : 0
                              }
                            />
                            <div className="text-sm text-muted-foreground">
                              {backgroundTask.total > 0
                                ? `${backgroundTask.current} / ${backgroundTask.total} `
                                : ''}
                              {backgroundTask.status}
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
                                  abortTaskAction(backgroundTask.task_id)
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
