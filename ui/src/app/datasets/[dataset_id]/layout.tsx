import Link from 'next/link';
import { Code, Columns, Eye, IterationCw, Settings } from 'lucide-react';
import { getClient } from '@/lib/api';
import { ErrorCard } from '@/components/error-card';
import { Breadcrumb } from './breadcrumb';
import { Tabs, TabsTrigger } from '@/components/ui/tabs';
import { TabsList } from '@/components/ui/tabs';
import { headers } from 'next/headers';

const getTab = (pathname: string) => {
  const tab = pathname.split('/').pop();
  if (tab === 'preview') return 'preview';
  if (tab === 'shardsets') return 'shardsets';
  if (tab === 'iterations') return 'iterations';
  if (tab === 'dataloader') return 'dataloader';
  if (tab === 'settings') return 'settings';
  return 'preview';
};

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
  const pathname = (await headers()).get('x-pathname') || '/';
  const tab = getTab(pathname);

  const client = await getClient();
  const datasetResponse = await client.GET('/datasets/{dataset_id}', {
    params: { path: { dataset_id } },
  });

  if (datasetResponse.error) {
    return <ErrorCard error={datasetResponse.error.detail} />;
  }

  const dataset = datasetResponse.data;

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center gap-8">
      <Breadcrumb />

      <div className="w-full flex flex-col gap-1">
        <div className="text-lg">{dataset.name}</div>
        <div className="text-xs text-muted-foreground">{dataset.id}</div>
      </div>

      <div className="w-full flex flex-col gap-2">
        <Tabs defaultValue={tab} className="w-full">
          <TabsList>
            <Link href={`/datasets/${dataset_id}/preview`}>
              <TabsTrigger value="preview">
                <div className="flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  Preview
                </div>
              </TabsTrigger>
            </Link>
            <Link href={`/datasets/${dataset_id}/shardsets`}>
              <TabsTrigger value="shardsets">
                <div className="flex items-center gap-1">
                  <Columns className="w-4 h-4" />
                  Shardsets
                </div>
              </TabsTrigger>
            </Link>
            <Link href={`/datasets/${dataset_id}/iterations`}>
              <TabsTrigger value="iterations">
                <div className="flex items-center gap-1">
                  <IterationCw className="w-4 h-4" />
                  Iterations
                </div>
              </TabsTrigger>
            </Link>
            <Link href={`/datasets/${dataset_id}/dataloader`}>
              <TabsTrigger value="dataloader">
                <div className="flex items-center gap-1">
                  <Code className="w-4 h-4" />
                  Dataloader
                </div>
              </TabsTrigger>
            </Link>
            <Link href={`/datasets/${dataset_id}/settings`}>
              <TabsTrigger value="settings">
                <div className="flex items-center gap-1">
                  <Settings className="w-4 h-4" />
                  Settings
                </div>
              </TabsTrigger>
            </Link>
          </TabsList>
        </Tabs>
        <div className="w-full">{children}</div>
      </div>
    </main>
  );
}
