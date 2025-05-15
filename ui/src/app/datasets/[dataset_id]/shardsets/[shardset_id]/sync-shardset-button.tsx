import { Button } from '@/components/ui/button';
import { RefreshCcw } from 'lucide-react';
import { syncShardset } from './sync-shardset-action';
import { getClient } from '@/lib/api';
import { redirect } from 'next/navigation';

export async function SyncShardsetButton({
  dataset_id,
  shardset_id,
}: {
  dataset_id: string;
  shardset_id: string;
}) {
  const syncStatusResponse = await (
    await getClient()
  ).GET('/datasets/{dataset_id}/shardsets/{shardset_id}/sync', {
    params: {
      path: {
        dataset_id,
        shardset_id,
      },
    },
  });

  const syncStatus = syncStatusResponse.data ? syncStatusResponse.data : null;

  const syncAction = async () => {
    'use server';
    await syncShardset(dataset_id, shardset_id, true);
    redirect(`/background-tasks/`);
  };

  return (
    <div className="w-full flex flex-col gap-1">
      <form action={syncAction}>
        <Button
          type="submit"
          className="w-full"
          disabled={!!syncStatus && syncStatus.status !== 'completed'}
        >
          <RefreshCcw className="w-4 h-4" />
          Sync
        </Button>
      </form>
    </div>
  );
}
