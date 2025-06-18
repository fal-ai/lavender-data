'use server';

import { getClient } from '@/lib/api';
import { revalidatePath } from 'next/cache';

export type ColumnInput = {
  name: string;
  type: string;
  description?: string;
};

export async function updateShardset(
  datasetId: string,
  shardsetId: string,
  is_main: boolean
) {
  try {
    const response = await (
      await getClient()
    ).PUT('/datasets/{dataset_id}/shardsets/{shardset_id}', {
      params: { path: { dataset_id: datasetId, shardset_id: shardsetId } },
      body: { is_main },
    });

    if (response.error) {
      let error = 'Unknown error';
      if (typeof response.error.detail === 'string') {
        error = response.error.detail;
      }
      return { success: false, error };
    }

    // Revalidate the dataset path to refresh the shardset list
    revalidatePath(`/datasets/${datasetId}/shardsets/${shardsetId}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'An unexpected error occurred',
    };
  }
}
