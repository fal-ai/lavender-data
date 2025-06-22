'use server';

import { getClient } from '@/lib/api';
import { revalidatePath } from 'next/cache';
import { ColumnInput } from './add-shardset-action';

export async function updateColumn(
  datasetId: string,
  columnId: string,
  column: Partial<ColumnInput>
) {
  try {
    const response = await (
      await getClient()
    ).PUT('/datasets/{dataset_id}/columns/{column_id}', {
      params: { path: { dataset_id: datasetId, column_id: columnId } },
      body: {
        name: column.name,
        type: column.type,
        description: column.description,
      },
    });
    revalidatePath(`/datasets/${datasetId}/shardsets`);
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return {
      success: false,
      error: 'Invalid column data',
    };
  }
}
