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

type DatasetPreviewResponse = components['schemas']['PreviewDatasetResponse'];

export const getDatasetPreview = async (
  datasetId: string,
  page: number,
  limit: number
): Promise<DatasetPreviewResponse> => {
  const response = await fetch(
    `/api/datasets/${datasetId}/preview?page=${page}&limit=${limit}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch dataset preview: ${response.status}`);
  }
  return response.json();
};

type FileType = components['schemas']['FileType'];

export const getFileType = async (fileUrl: string): Promise<FileType> => {
  const response = await fetch(`/api/files/type?file_url=${fileUrl}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch file: ${response.status}`);
  }
  return response.json();
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
    throw new Error(`Failed to start iteration: ${response.status}`);
  }
  return response.json();
};

export const getIterationNextPreview = async (iterationId: string) => {
  const response = await fetch(`/api/iterations/${iterationId}/next-preview`);
  if (!response.ok) {
    throw new Error(
      `Failed to fetch iteration next preview: ${response.status}`
    );
  }
  return response.json();
};
