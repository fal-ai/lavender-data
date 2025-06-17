'use client';

import Link from 'next/link';
import { Code, Columns, Eye, IterationCw, Settings } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { usePathname } from 'next/navigation';

const getTab = (pathname: string) => {
  const tab = pathname.split('/').pop();
  if (tab === 'preview') return 'preview';
  if (tab === 'shardsets') return 'shardsets';
  if (tab === 'iterations') return 'iterations';
  if (tab === 'dataloader') return 'dataloader';
  if (tab === 'settings') return 'settings';
  return 'preview';
};

export function DatasetNavTabs({ dataset_id }: { dataset_id: string }) {
  const pathname = usePathname();
  const tab = getTab(pathname);

  return (
    <Tabs value={tab} className="w-full">
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
  );
}
