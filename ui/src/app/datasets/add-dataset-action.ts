'use server';

import { getClient } from '@/lib/api';
import { revalidatePath } from 'next/cache';

export async function createDataset(formData: FormData) {
  const name = formData.get('name') as string;
  const uidColumnName = formData.get('uidColumnName') as string;
  const shardsetLocation = formData.get('shardsetLocation') as string;

  if (!name) {
    return { success: false, error: 'Name is required' };
  }

  if (!uidColumnName) {
    return { success: false, error: 'UID column name is required' };
  }

  try {
    const response = await (
      await getClient()
    ).POST('/datasets/', {
      body: {
        name,
        uid_column_name: uidColumnName,
        shardset_location: shardsetLocation,
      },
    });

    if (response.error) {
      let error = 'Unknown error';
      if (typeof response.error.detail === 'string') {
        error = response.error.detail;
      }
      return { success: false, error };
    }

    // Revalidate the datasets path to refresh the list
    revalidatePath('/datasets');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'An unexpected error occurred',
    };
  }
}
