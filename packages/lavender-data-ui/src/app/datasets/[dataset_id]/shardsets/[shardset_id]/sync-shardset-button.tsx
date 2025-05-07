'use client';

import type { components } from '@/lib/api/v1';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { RefreshCcw } from 'lucide-react';
import { syncShardset } from './sync-shardset-action';
import { Progress } from '@/components/ui/progress';
import { useRouter } from 'next/navigation';
import { getSyncShardsetStatus } from '@/lib/client-side-api';

type SyncShardsetStatus = components['schemas']['SyncShardsetStatus'];

export function SyncShardsetButton({
  dataset_id,
  shardset_id,
}: {
  dataset_id: string;
  shardset_id: string;
}) {
  const [syncStatus, setSyncStatus] = useState<SyncShardsetStatus | null>(null);
  const [intervalRef, setIntervalRef] = useState<NodeJS.Timeout | null>(null);
  const router = useRouter();

  const refreshStatus = async () => {
    try {
      const response = await getSyncShardsetStatus(dataset_id, shardset_id);
      setSyncStatus(response);
    } catch (error) {
      console.error('error', error);
      setSyncStatus(null);
    }
  };

  useEffect(() => {
    refreshStatus();

    return () => {
      if (intervalRef != null) {
        clearInterval(intervalRef);
        setIntervalRef(null);
      }
    };
  }, []);

  useEffect(() => {
    if (
      intervalRef == null &&
      syncStatus != null &&
      syncStatus.status != 'done'
    ) {
      setIntervalRef(setInterval(() => refreshStatus(), 100));
    } else if (
      intervalRef != null &&
      (syncStatus == null || syncStatus.status == 'done')
    ) {
      clearInterval(intervalRef);
      setIntervalRef(null);
      router.refresh();
    }
  }, [syncStatus, intervalRef]);

  const clientSyncAction = async () => {
    await syncShardset(dataset_id, shardset_id, true);
    await refreshStatus();
    setIntervalRef(setInterval(() => refreshStatus(), 100));
  };

  return (
    <div className="w-full flex flex-col gap-1">
      <form action={clientSyncAction}>
        <Button type="submit" className="w-full" disabled={!!syncStatus}>
          <RefreshCcw className="w-4 h-4" />
          Sync
        </Button>
      </form>
      <div className="h-[20px]">
        {syncStatus && (
          <div className="grid grid-cols-[80px_1fr] gap-2 items-center">
            <Progress
              className="w-full"
              value={
                syncStatus.shard_count > 0
                  ? (100 * syncStatus.done_count) / syncStatus.shard_count
                  : 0
              }
            />
            <div className="text-sm text-muted-foreground">
              {syncStatus.shard_count > 0
                ? `${syncStatus.done_count} / ${syncStatus.shard_count} `
                : ''}
              {syncStatus.status}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
