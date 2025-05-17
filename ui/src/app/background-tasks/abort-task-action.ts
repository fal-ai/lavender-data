'use server';

import { getClient } from '@/lib/api';

export async function abortTask(taskId: string) {
  try {
    const response = await (
      await getClient()
    ).POST('/background-tasks/{task_uid}/abort', {
      params: { path: { task_uid: taskId } },
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
