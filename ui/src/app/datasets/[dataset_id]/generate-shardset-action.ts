'use server';

import { getClient } from '@/lib/api';

export async function generateShardset(
  datasetId: string,
  shardsetLocation: string,
  sourceShardsetIds: string[],
  preprocessorsJson: string,
  exportColumns: string[],
  batchSize: number,
  overwrite: boolean
) {
  let preprocessors: {
    name: string;
    params: {
      [key: string]: unknown;
    };
  }[] = [];

  try {
    preprocessors = JSON.parse(preprocessorsJson);
  } catch (error) {
    return {
      success: false,
      error: 'Invalid preprocessors data',
    };
  }

  try {
    const response = await (
      await getClient()
    ).POST('/datasets/{dataset_id}/generate-shardset', {
      params: { path: { dataset_id: datasetId } },
      body: {
        shardset_location: shardsetLocation,
        source_shardset_ids: sourceShardsetIds,
        preprocessors: preprocessors,
        export_columns: exportColumns,
        batch_size: batchSize,
        overwrite: overwrite,
      },
    });

    if (response.error) {
      let error = 'Unknown error';
      if (typeof response.error.detail === 'string') {
        error = response.error.detail;
      }
      return { success: false, error };
    }

    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'An unexpected error occurred',
    };
  }
}
