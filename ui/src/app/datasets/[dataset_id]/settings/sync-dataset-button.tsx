import { Button } from '@/components/ui/button';
import { RefreshCcw } from 'lucide-react';
import { syncShardset } from '../shardsets/[shardset_id]/sync-shardset-action';
import { getClient } from '@/lib/api';
import { redirect } from 'next/navigation';

export async function SyncDatasetButton({
  dataset_id,
  shardsets,
}: {
  dataset_id: string;
  shardsets: string[];
}) {
  const syncStatusResponses = await Promise.all(
    shardsets.map(async (shardset_id) => {
      const client = await getClient();
      return client.GET('/datasets/{dataset_id}/shardsets/{shardset_id}/sync', {
        params: {
          path: {
            dataset_id,
            shardset_id,
          },
        },
      });
    })
  );

  const disabled = !!syncStatusResponses.find(
    (response) => response.data && response.data.status !== 'completed'
  );

  const syncAction = async () => {
    'use server';
    const client = await getClient();
    const datasetResponse = await client.GET('/datasets/{dataset_id}', {
      params: { path: { dataset_id } },
    });
    if (datasetResponse.error) {
      return;
    }
    const dataset = datasetResponse.data;
    const shardsets = dataset.shardsets.map((s) => s.id as string);
    await Promise.all(
      shardsets.map((shardset_id) =>
        syncShardset(dataset_id, shardset_id, false)
      )
    );
    redirect(`/background-tasks/`);
  };

  return (
    <div className="w-full flex flex-col gap-1">
      <form action={syncAction}>
        <Button type="submit" className="w-full" disabled={disabled}>
          <RefreshCcw className="w-4 h-4" />
          Sync
        </Button>
      </form>
    </div>
  );
}
