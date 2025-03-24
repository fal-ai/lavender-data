import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import Link from 'next/link';
import { client } from '@/lib/api';
import { utcToLocal } from '@/lib/date';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AddDatasetDialog } from './add-dataset-dialog';
import { ErrorCard } from '@/components/error-card';
export default async function DatasetsPage() {
  const datasetsResponse = await client.GET('/datasets/');

  if (datasetsResponse.error) {
    return <ErrorCard error={datasetsResponse.error.detail} />;
  }

  const datasets = datasetsResponse.data;

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center space-y-8 py-10">
      <div className="w-full flex flex-col gap-2">
        <div className="text-lg">Datasets</div>
      </div>
      <Table className="w-full">
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
                <Link href={`/datasets/${dataset.id}`}>{dataset.id}</Link>
              </TableCell>
              <TableCell>{dataset.name}</TableCell>
              <TableCell>{utcToLocal(dataset.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="w-full flex justify-end gap-2">
        <AddDatasetDialog>
          <Button variant="outline">
            <Plus />
            Dataset
          </Button>
        </AddDatasetDialog>
      </div>
    </main>
  );
}
