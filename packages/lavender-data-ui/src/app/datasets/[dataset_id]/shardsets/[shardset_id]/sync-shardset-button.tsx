'use client';

import { client } from '@/lib/api';
import type { components } from '@/lib/api/v1';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { RefreshCcw } from 'lucide-react';
import { syncShardset } from './sync-shardset-action';
import { Progress } from '@/components/ui/progress';

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

  const refreshStatus = async () => {
    try {
      const response = await client.GET(
        '/datasets/{dataset_id}/shardsets/{shardset_id}/sync',
        {
          params: { path: { dataset_id, shardset_id } },
        }
      );
      if (response.data) {
        setSyncStatus(response.data);
      } else {
        setSyncStatus(null);
      }
    } catch (error) {
      setSyncStatus(null);
    }
  };

  useEffect(() => {
    refreshStatus();
  }, []);

  useEffect(() => {
    if (syncStatus != null && intervalRef == null) {
      setIntervalRef(setInterval(() => refreshStatus(), 100));
    } else if (syncStatus == null && intervalRef != null) {
      clearInterval(intervalRef);
      setIntervalRef(null);
    }
  }, [syncStatus]);

  const clientSyncAction = async () => {
    await syncShardset(dataset_id, shardset_id, true);
    await refreshStatus();
    setIntervalRef(setInterval(() => refreshStatus(), 100));
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="h-4">
        {syncStatus && (
          <div className="flex items-center gap-2">
            <Progress
              className="w-80"
              value={
                syncStatus.shard_count > 0
                  ? (100 * syncStatus.done_count) / syncStatus.shard_count
                  : 0
              }
            />
            <div className="text-sm text-muted-foreground">
              {syncStatus.status}
            </div>
            <div className="text-sm text-muted-foreground">
              {syncStatus.shard_count > 0
                ? `${syncStatus.done_count} / ${syncStatus.shard_count}`
                : ''}
            </div>
          </div>
        )}
      </div>
      <form action={clientSyncAction}>
        <Button type="submit" disabled={!!syncStatus}>
          <RefreshCcw className="w-4 h-4" />
          Sync
        </Button>
      </form>
    </div>
  );
}
