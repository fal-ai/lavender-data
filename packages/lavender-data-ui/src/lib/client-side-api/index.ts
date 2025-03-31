import { type components } from '@/lib/api/v1';

type VersionResponse = components['schemas']['VersionResponse'];

export const getVersion = async (): Promise<VersionResponse> => {
  const response = await fetch('/api/version');
  if (!response.ok) {
    throw new Error('Failed to fetch version');
  }
  return response.json();
};

type SyncShardsetStatus = components['schemas']['SyncShardsetStatus'];

export const getSyncShardsetStatus = async (
  datasetId: string,
  shardsetId: string
): Promise<SyncShardsetStatus> => {
  const response = await fetch(
    `/api/datasets/${datasetId}/shardsets/${shardsetId}/sync`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch shardset sync status: ${response.status}`);
  }
  return response.json();
};
