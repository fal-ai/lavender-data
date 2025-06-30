import { getClient } from '@/lib/api';
import { ErrorCard } from '@/components/error-card';
import { DatasetNavTabs } from './nav-tabs';
import { formatNumber } from '@/lib/number';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@/components/ui/table';

export default async function DatasetDetailPageLayout({
  params,
  children,
}: {
  params: Promise<{
    dataset_id: string;
  }>;
  children: React.ReactNode;
}) {
  const { dataset_id } = await params;

  const client = await getClient();
  const datasetResponse = await client.GET('/datasets/{dataset_id}', {
    params: { path: { dataset_id } },
  });

  if (datasetResponse.error) {
    return <ErrorCard error={datasetResponse.error.detail} />;
  }

  const dataset = datasetResponse.data;
  const shardMinCount = Math.min(
    ...dataset.shardsets.map((s) => s.shard_count)
  );
  const shardMaxCount = Math.max(
    ...dataset.shardsets.map((s) => s.shard_count)
  );
  const samplesMin = Math.min(...dataset.shardsets.map((s) => s.total_samples));
  const samplesMax = Math.max(...dataset.shardsets.map((s) => s.total_samples));

  return (
    <div className="w-full flex flex-col gap-2">
      <div className="w-full flex flex-col gap-4 pb-4">
        <div className="w-full flex flex-col gap-1">
          <div className="text-lg">{dataset.name}</div>
          <div className="text-xs text-muted-foreground">{dataset.id}</div>
        </div>
        <Table className="w-[400px]">
          <TableBody>
            <TableRow>
              <TableHead>columns</TableHead>
              <TableCell>{dataset.columns.length}</TableCell>
            </TableRow>
            <TableRow>
              <TableHead>shardsets</TableHead>
              <TableCell>{dataset.shardsets.length}</TableCell>
            </TableRow>
            <TableRow>
              <TableHead>shards</TableHead>
              <TableCell>
                {shardMinCount === shardMaxCount
                  ? `${shardMinCount} `
                  : `${shardMinCount} - ${shardMaxCount} `}
                per shardset
              </TableCell>
            </TableRow>
            <TableRow>
              <TableHead>samples</TableHead>
              <TableCell>
                {samplesMin === samplesMax
                  ? `${formatNumber(samplesMin)} `
                  : `${formatNumber(samplesMin)} - ${formatNumber(samplesMax)} `}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>

      <div className="w-full flex flex-col gap-2">
        <DatasetNavTabs dataset_id={dataset_id} />
        <div className="w-full">{children}</div>
      </div>
    </div>
  );
}
