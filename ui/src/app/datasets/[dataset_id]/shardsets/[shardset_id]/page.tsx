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
import { ChevronLeft, Columns, FileStack, Settings } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DeleteShardsetDialog } from './delete-shardset-dialog';
import { Button } from '@/components/ui/button';
import { Pagination } from '@/components/pagination';
import { SetAsMainSwitch } from './set-as-main-switch';

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) {
    return `${bytes} B`;
  } else if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`;
  } else if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  } else if (bytes < 1024 * 1024 * 1024 * 1024) {
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  } else {
    return `${(bytes / 1024 / 1024 / 1024 / 1024).toFixed(2)} TB`;
  }
};

export default async function ShardsetDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{
    dataset_id: string;
    shardset_id: string;
  }>;
  searchParams: Promise<{
    tab: string;
    shards_page: string;
  }>;
}) {
  const { dataset_id, shardset_id } = await params;
  const { tab = 'columns', shards_page = '0' } = await searchParams;
  const client = await getClient();
  const shardsetResponse = await client.GET(
    '/datasets/{dataset_id}/shardsets/{shardset_id}',
    {
      params: { path: { dataset_id, shardset_id } },
    }
  );

  if (shardsetResponse.error) {
    return <ErrorCard error={shardsetResponse.error.detail} />;
  }

  const shardsLimit = 10;
  const shardsResponse = await client.GET(
    '/datasets/{dataset_id}/shardsets/{shardset_id}/shards',
    {
      params: {
        path: { dataset_id, shardset_id },
        query: {
          offset: Number(shards_page) * shardsLimit,
          limit: shardsLimit,
        },
      },
    }
  );

  if (shardsResponse.error) {
    return <ErrorCard error={shardsResponse.error.detail} />;
  }

  const shardset = shardsetResponse.data;
  const shards = shardsResponse.data.shards;
  const shardsTotal = shardsResponse.data.total;

  return (
    <div className="py-4 flex w-full flex-1 flex-col gap-8">
      <div className="flex items-center gap-2">
        <Button variant="ghost">
          <Link href={`/datasets/${dataset_id}/shardsets`}>
            <ChevronLeft className="w-4 h-4" />
          </Link>
        </Button>
        <div className="flex flex-col gap-2">
          <div className="text-md">{shardset.location}</div>
          <div className="text-xs text-muted-foreground">{shardset.id}</div>
        </div>
      </div>

      <Tabs defaultValue={tab} className="w-full">
        <TabsList>
          <Link
            href={`/datasets/${dataset_id}/shardsets/${shardset_id}?tab=columns`}
          >
            <TabsTrigger value="columns">
              <div className="flex items-center gap-1">
                <Columns className="w-4 h-4" />
                Columns
              </div>
            </TabsTrigger>
          </Link>
          <Link
            href={`/datasets/${dataset_id}/shardsets/${shardset_id}?tab=shards`}
          >
            <TabsTrigger value="shards">
              <div className="flex items-center gap-1">
                <FileStack className="w-4 h-4" />
                Shards
              </div>
            </TabsTrigger>
          </Link>
          <Link
            href={`/datasets/${dataset_id}/shardsets/${shardset_id}?tab=settings`}
          >
            <TabsTrigger value="settings">
              <div className="flex items-center gap-1">
                <Settings className="w-4 h-4" />
                Settings
              </div>
            </TabsTrigger>
          </Link>
        </TabsList>
        <TabsContent value="columns" className="flex flex-col gap-2">
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
        </TabsContent>
        <TabsContent value="shards" className="flex flex-col gap-2">
          <div className="text-xs text-muted-foreground">
            {shardsTotal} shards, {shardset.total_samples} samples
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
                  {shards
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
                        <TableCell>{formatFileSize(shard.filesize)}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
              <div className="w-full flex items-center pt-4">
                <Pagination
                  buttonCount={5}
                  totalPages={Math.ceil(shardsTotal / shardsLimit)}
                  currentPage={Number(shards_page)}
                  pageHref={`/datasets/${dataset_id}/shardsets/${shardset_id}?tab=shards&shards_page={page}`}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent
          value="settings"
          className="w-full max-w-[720px] flex flex-col gap-2 items-start"
        >
          <Card className="w-full">
            <CardContent className="flex flex-col gap-2">
              <div className="grid grid-cols-[1fr_200px] gap-2">
                <div>
                  <div className="text-md">Set as main shardset</div>
                  <div className="text-xs text-muted-foreground">
                    Set this shardset as the main shardset for the dataset.
                    <a
                      href="https://docs.lavenderdata.com/dataset/join-method/#main-shard-and-feature-shards"
                      className="underline ml-1"
                      target="_blank"
                    >
                      More info
                    </a>
                  </div>
                </div>
                <SetAsMainSwitch
                  dataset_id={dataset_id}
                  shardset_id={shardset_id}
                  is_main={shardset.is_main}
                />
              </div>
              <div className="grid grid-cols-[1fr_200px] gap-2">
                <div>
                  <div className="text-md">Sync shardset</div>
                  <div className="text-xs text-muted-foreground">
                    Sync the shardset to its location.
                  </div>
                </div>
                <SyncShardsetButton
                  dataset_id={dataset_id}
                  shardset_id={shardset_id}
                />
              </div>
              <div className="grid grid-cols-[1fr_200px] gap-2">
                <div>
                  <div className="text-md">Delete this shardset</div>
                  <div className="text-xs text-muted-foreground">
                    This action is irreversible.
                  </div>
                </div>
                <DeleteShardsetDialog
                  datasetId={dataset_id}
                  shardsetId={shardset_id}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
