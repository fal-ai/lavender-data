import { type components } from '@/lib/api/v1';

type VersionResponse = components['schemas']['VersionResponse'];

export const getVersion = async (): Promise<VersionResponse> => {
  const response = await fetch('/api/version');
  if (!response.ok) {
    throw new Error('Failed to fetch version');
  }
  return response.json();
};

type TaskStatus = components['schemas']['TaskStatus'];
type TaskMetadata = components['schemas']['TaskMetadata'];

export const getSyncShardsetStatus = async (
  datasetId: string,
  shardsetId: string
): Promise<TaskStatus | null> => {
  const response = await fetch(
    `/api/datasets/${datasetId}/shardsets/${shardsetId}/sync`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch shardset sync status: ${response.status}`);
  }
  return response.json();
};

export const getBackgroundTasks = async (): Promise<TaskMetadata[]> => {
  const response = await fetch(`/api/background-tasks`);
  if (!response.ok) {
    throw new Error(`Failed to fetch background tasks: ${response.status}`);
  }
  return response.json();
};

type CreateDatasetPreviewResponse =
  components['schemas']['CreateDatasetPreviewResponse'];

export const createDatasetPreview = async (
  datasetId: string,
  offset: number,
  limit: number
): Promise<CreateDatasetPreviewResponse> => {
  const response = await fetch(`/api/datasets/${datasetId}/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      offset,
      limit,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch dataset preview: ${response.status}`);
  }
  return response.json();
};

type GetDatasetPreviewResponse =
  components['schemas']['GetDatasetPreviewResponse'];

export const getDatasetPreview = async (
  datasetId: string,
  previewId: string
): Promise<GetDatasetPreviewResponse> => {
  const response = await fetch(
    `/api/datasets/${datasetId}/preview/${previewId}`
  );
  if (!response.ok) {
    throw new Error(
      `Failed to fetch dataset preview: ${await getError(response)}`
    );
  }
  return response.json();
};

const getError = async (response: Response) => {
  try {
    return `${response.status} ${(await response.json()).detail}`;
  } catch (e) {
    return `${response.status} ${await response.text()}`;
  }
};

export const createIteration = async (
  datasetId: string,
  dataloaderParams: Record<string, any>
) => {
  const response = await fetch(`/api/iterations`, {
    method: 'POST',
    body: JSON.stringify({ dataset_id: datasetId, ...dataloaderParams }),
  });
  if (!response.ok) {
    throw new Error(`Failed to start iteration: ${await getError(response)}`);
  }
  return response.json();
};

export const getIterationNextPreview = async (iterationId: string) => {
  const response = await fetch(`/api/iterations/${iterationId}/next-preview`);
  if (!response.ok) {
    throw new Error(
      `Failed to fetch iteration next preview: ${await getError(response)}`
    );
  }
  return response.json();
};
