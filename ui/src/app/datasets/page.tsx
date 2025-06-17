import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import Link from 'next/link';
import { getClient } from '@/lib/api';
import { utcToLocal } from '@/lib/date';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AddDatasetDialog } from './add-dataset-dialog';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent } from '@/components/ui/card';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

export default async function DatasetsPage() {
  const datasetsResponse = await (await getClient()).GET('/datasets/');

  if (datasetsResponse.error) {
    return <ErrorCard error={datasetsResponse.error.detail} />;
  }

  const datasets = datasetsResponse.data;

  return (
    <div className="w-full flex flex-col gap-2">
      <div className="text-lg">Datasets</div>
      {datasets.length > 0 ? (
        <Card className="w-full">
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead className="min-w-[200px]">Name</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datasets.map((dataset: any) => (
                  <TableRow key={dataset.id}>
                    <TableCell className="font-mono text-xs">
                      <Link href={`/datasets/${dataset.id}/preview`}>
                        {dataset.id}
                      </Link>
                    </TableCell>
                    <TableCell>{dataset.name}</TableCell>
                    <TableCell>{utcToLocal(dataset.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : (
        <div className="text-center text-muted-foreground m-8">
          Nothing here yet.
        </div>
      )}
      <div className="w-full flex justify-end gap-2">
        <AddDatasetDialog>
          <Button variant="outline">
            <Plus />
            Dataset
          </Button>
        </AddDatasetDialog>
      </div>
    </div>
  );
}
