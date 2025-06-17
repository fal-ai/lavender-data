import { Button } from '@/components/ui/button';
import { getClient } from '@/lib/api';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent } from '@/components/ui/card';
import { DeleteDatasetDialog } from './delete-dataset-dialog';
import { PreprocessDatasetDialog } from './preprocess-dataset-dialog';
import { SyncDatasetButton } from './sync-dataset-button';

export default async function DatasetSettingsPage({
  params,
}: {
  params: Promise<{
    dataset_id: string;
  }>;
}) {
  const { dataset_id } = await params;
  const client = await getClient();
  const datasetResponse = await client.GET('/datasets/{dataset_id}', {
    params: { path: { dataset_id } },
  });
  const preprocessorsResponse = await client.GET(
    '/registries/preprocessors',
    {}
  );

  if (datasetResponse.error) {
    return <ErrorCard error={datasetResponse.error.detail} />;
  }

  if (!preprocessorsResponse.data) {
    return <ErrorCard error={preprocessorsResponse.error} />;
  }

  const dataset = datasetResponse.data;

  return (
    <div className="w-full max-w-[720px] flex flex-col gap-2 items-start">
      <Card className="w-full">
        <CardContent className="flex flex-col gap-2">
          <div className="grid grid-cols-[1fr_200px] gap-2">
            <div>
              <div className="text-md">Sync shardsets</div>
              <div className="text-xs text-muted-foreground">
                Sync the all shardsets of this dataset to their locations.
              </div>
            </div>
            <SyncDatasetButton
              dataset_id={dataset_id}
              shardsets={dataset.shardsets.map((s) => s.id as string)}
            />
          </div>
          <div className="grid grid-cols-[1fr_200px] gap-2">
            <div>
              <div className="text-md">Preprocess</div>
              <div className="text-xs text-muted-foreground">
                Generate a new shardset by preprocessing the dataset.
              </div>
            </div>
            <PreprocessDatasetDialog
              datasetId={dataset_id}
              shardsets={
                dataset.shardsets as {
                  id: string;
                  location: string;
                }[]
              }
              preprocessors={preprocessorsResponse.data.map(
                (preprocessor) => preprocessor.name
              )}
            >
              <Button variant="default">Preprocess</Button>
            </PreprocessDatasetDialog>
          </div>
          <div className="grid grid-cols-[1fr_200px] gap-2">
            <div>
              <div className="text-md">Delete this dataset</div>
              <div className="text-xs text-muted-foreground">
                This action is irreversible.
              </div>
            </div>
            <DeleteDatasetDialog datasetId={dataset_id}>
              <Button variant="destructive">Delete this dataset</Button>
            </DeleteDatasetDialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
