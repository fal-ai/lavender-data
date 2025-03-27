'use server';

import { client } from '@/lib/api';
import { revalidatePath } from 'next/cache';

export type ColumnInput = {
  name: string;
  type: string;
  description?: string;
};

export async function createShardset(datasetId: string, formData: FormData) {
  const location = formData.get('location') as string;
  const columnsJson = formData.get('columnsJson') as string;
  let columns: ColumnInput[] = [];

  try {
    columns = JSON.parse(columnsJson);
  } catch (error) {
    return {
      success: false,
      error: 'Invalid column data',
    };
  }

  if (!location) {
    return { success: false, error: 'Location is required' };
  }

  if (columns.some((column) => column.name === '')) {
    return { success: false, error: 'All columns must have a name' };
  }

  if (columns.some((column) => column.type === '')) {
    return { success: false, error: 'All columns must have a type' };
  }

  try {
    const response = await client.POST('/datasets/{dataset_id}/shardsets', {
      params: { path: { dataset_id: datasetId } },
      body: {
        location,
        columns,
      },
    });

    if (response.error) {
      let error = 'Unknown error';
      if (typeof response.error.detail === 'string') {
        error = response.error.detail;
      }
      return { success: false, error };
    }

    // Revalidate the dataset path to refresh the shardset list
    revalidatePath(`/datasets/${datasetId}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'An unexpected error occurred',
    };
  }
}
