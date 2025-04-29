import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { getClient } from '@/lib/api';
import { ErrorCard } from '@/components/error-card';
import Link from 'next/link';
import { SyncShardsetButton } from './sync-shardset-button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

export default async function ShardsetDetailPage({
  params,
}: {
  params: Promise<{
    dataset_id: string;
    shardset_id: string;
  }>;
}) {
  const { dataset_id, shardset_id } = await params;
  const shardsetResponse = await (
    await getClient()
  ).GET('/datasets/{dataset_id}/shardsets/{shardset_id}', {
    params: { path: { dataset_id, shardset_id } },
  });

  if (shardsetResponse.error) {
    return <ErrorCard error={shardsetResponse.error.detail} />;
  }

  const shardset = shardsetResponse.data;

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center gap-8">
      <Breadcrumb className="w-full pt-4">
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Home</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href="/datasets">Datasets</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href={`/datasets/${shardset.dataset_id}`}>
              {shardset.dataset_id}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href={`/datasets/${shardset.dataset_id}`}>
              Shardsets
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{shardset.id}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="w-full flex flex-col gap-1">
        <div className="text-lg">{shardset.location}</div>
        <div className="text-xs text-muted-foreground">{shardset.id}</div>
      </div>

      <div className="w-full flex flex-col gap-2">
        <SyncShardsetButton dataset_id={dataset_id} shardset_id={shardset_id} />
      </div>

      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Columns</div>
        <div className="text-xs text-muted-foreground">
          {shardset.columns.length} columns
        </div>
        <Card className="w-full">
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shardset.columns.map((column) => (
                  <TableRow key={column.id}>
                    <TableCell className="font-mono text-xs">
                      {column.name}
                    </TableCell>
                    <TableCell>{column.type}</TableCell>
                    <TableCell>{column.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Shards</div>
        <div className="text-xs text-muted-foreground">
          {shardset.shard_count} shards, {shardset.total_samples} samples
        </div>
        <Card className="w-full">
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">ID</TableHead>
                  <TableHead>Index</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Format</TableHead>
                  <TableHead>Samples</TableHead>
                  <TableHead>Filesize</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shardset.shards
                  .sort((a, b) => a.index - b.index) // TODO server side sorting
                  .map((shard) => (
                    <TableRow key={shard.id}>
                      <TableCell className="font-mono text-xs">
                        {shard.id}
                      </TableCell>
                      <TableCell>{shard.index}</TableCell>
                      <TableCell>{shard.location}</TableCell>
                      <TableCell>{shard.format}</TableCell>
                      <TableCell>{shard.samples}</TableCell>
                      <TableCell>{shard.filesize}</TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
