'use client';

import { useState, useEffect } from 'react';
import { Pagination } from '@/components/pagination';
import { ErrorCard } from '@/components/error-card';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { getDatasetPreview } from '@/lib/client-side-api';
import type { components } from '@/lib/api/v1';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { LoaderCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MultiSelect } from '@/components/multiselect';
import SamplesTable from '../samples-table';

type DatasetPreviewResponse = components['schemas']['PreviewDatasetResponse'];

const getColumnsFromLocalStorage = (
  dataset_id: string
): { name: string; selected: boolean }[] => {
  if (typeof window !== 'undefined') {
    const storage = localStorage.getItem(`columns-${dataset_id}`);
    if (storage) {
      return JSON.parse(storage);
    }
  }
  return [];
};

const setColumnsToLocalStorage = (
  dataset_id: string,
  columns: { name: string; selected: boolean }[]
) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(`columns-${dataset_id}`, JSON.stringify(columns));
  }
};

export default function DatasetPreviewPage({}: {}) {
  const { dataset_id } = useParams() as { dataset_id: string };
  const searchParams = useSearchParams();

  const router = useRouter();

  const preview_limit = 20;
  const preview_page = Number(searchParams.get('preview_page')) || 0;
  const currentPage = Number(preview_page);
  const columnsParams = searchParams.get('columns') || '';
  const [totalPages, setTotalPages] = useState<number>(0);

  const [columns, setColumns] = useState<
    {
      name: string;
      selected: boolean;
    }[]
  >([]);
  const [preview, setPreview] = useState<DatasetPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDatasetPreview(dataset_id, preview_page, preview_limit)
      .then((r) => {
        const totalPages = Math.ceil(r.total / preview_limit);
        const fetchedColumns = r.columns.map((column) => column.name);
        const storedColumns = getColumnsFromLocalStorage(dataset_id);
        const paramsColumns =
          storedColumns.length > 0
            ? storedColumns
            : columnsParams
                .split(',')
                .filter((c) => c !== '')
                .map((c) => {
                  const [name, selected] = c.split('||');
                  return {
                    name: name,
                    selected: selected === '1',
                  };
                });

        setPreview(r);
        setTotalPages(totalPages);

        if (paramsColumns.length === 0) {
          setColumns(
            fetchedColumns.map((c) => ({
              name: c,
              selected: true,
            }))
          );
        } else {
          setColumns(paramsColumns);
        }
      })
      .catch((e) => {
        setError(e.message);
      });
  }, [dataset_id, preview_page, preview_limit]);

  useEffect(() => {
    if (columns.length > 0) {
      router.push(
        `/datasets/${dataset_id}/preview?preview_page=${currentPage}&columns=${columns
          .map((c) => `${c.name}||${c.selected ? '1' : '0'}`)
          .join(',')}`
      );
      setColumnsToLocalStorage(dataset_id, columns);
    }
  }, [columns]);

  if (error) {
    return (
      <ErrorCard
        error={`Preview is not available for this dataset. ${error ? error : ''}`}
      />
    );
  }

  if (!preview) {
    return (
      <div className="w-full flex gap-2 p-4 justify-center items-center text-muted-foreground">
        <LoaderCircle className="w-4 h-4 animate-spin" />
        <div className="text-sm">Loading...</div>
      </div>
    );
  }

  return (
    <Card className="w-full">
      <CardContent className="w-full">
        <div className="w-full flex justify-start mb-4">
          <div className="flex gap-2">
            <MultiSelect
              label="Columns"
              placeholder="Search columns..."
              emptyText="No columns found"
              draggable={true}
              value={columns.map((c) => ({
                label: c.name,
                value: c.name,
                selected: c.selected,
              }))}
              onChange={(value) =>
                setColumns(
                  value.map((v) => ({
                    name: v.value,
                    selected: v.selected,
                  }))
                )
              }
            />
            <Button
              variant="outline"
              onClick={() =>
                setColumns(
                  preview.columns.map((column) => ({
                    name: column.name,
                    selected: true,
                  }))
                )
              }
            >
              Reset
            </Button>
          </div>
        </div>
        <SamplesTable
          samples={preview.samples}
          columns={columns.filter((c) => c.selected).map((c) => c.name)}
        />
      </CardContent>
      <CardFooter className="w-full flex justify-center">
        <Pagination
          buttonCount={10}
          totalPages={totalPages}
          currentPage={currentPage}
          pageHref={`/datasets/${dataset_id}/preview?preview_page={page}`}
        />
      </CardFooter>
    </Card>
  );
}
