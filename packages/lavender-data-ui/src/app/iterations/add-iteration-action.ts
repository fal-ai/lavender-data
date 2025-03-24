'use server';

import { client } from '@/lib/api';
import { revalidatePath } from 'next/cache';

export async function createIteration(formData: FormData) {
  // Extract values from form data
  const datasetId = formData.get('datasetId') as string;
  const shardsetsJson = formData.get('shardsetsJson') as string;
  const preprocessor = formData.get('preprocessor') as string;
  const filter = formData.get('filter') as string;
  const collater = formData.get('collater') as string;
  const shuffle = formData.get('shuffle') === 'true';
  const shuffleSeed = parseInt(formData.get('shuffleSeed') as string, 10) || 0;
  const shuffleBlockSize =
    parseInt(formData.get('shuffleBlockSize') as string, 10) || 1;
  const batchSize = parseInt(formData.get('batchSize') as string, 10) || 0;
  const replicationPgStr = formData.get('replicationPg') as string;

  let shardsets: string[] = [];
  let replicationPg = null;

  if (!datasetId) {
    return { success: false, error: 'Dataset is required' };
  }

  try {
    if (shardsetsJson) {
      shardsets = JSON.parse(shardsetsJson);
    }
  } catch (error) {
    return { success: false, error: 'Invalid shardsets data' };
  }

  try {
    if (replicationPgStr) {
      replicationPg = JSON.parse(replicationPgStr);
    }
  } catch (error) {
    return { success: false, error: 'Replication is invalid' };
  }

  try {
    const response = await client.POST('/iterations/', {
      body: {
        dataset_id: datasetId,
        shardsets,
        preprocessor: preprocessor || null,
        filter: filter || null,
        collater: collater || null,
        shuffle,
        shuffle_seed: shuffleSeed,
        shuffle_block_size: shuffleBlockSize,
        batch_size: batchSize,
        replication_pg: replicationPg,
      },
    });

    if (response.error) {
      let error = 'Unknown error';
      if (typeof response.error.detail === 'string') {
        error = response.error.detail;
      }
      return { success: false, error };
    }

    // Revalidate the iterations path to refresh the list
    revalidatePath('/iterations');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'An unexpected error occurred',
    };
  }
}
