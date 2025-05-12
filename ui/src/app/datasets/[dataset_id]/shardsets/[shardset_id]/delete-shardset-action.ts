'use server';

import { getClient } from '@/lib/api';

export async function deleteShardset(datasetId: string, shardsetId: string) {
  try {
    const response = await (
      await getClient()
    ).DELETE('/datasets/{dataset_id}/shardsets/{shardset_id}', {
      params: { path: { dataset_id: datasetId, shardset_id: shardsetId } },
    });

    if (response.error) {
      return { success: false, error: response.error.detail };
    }

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'An unexpected error occurred',
    };
  }
}
