'use client';

import { isInteger } from 'lodash';
import { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Pagination } from '@/components/pagination';
import { ErrorCard } from '@/components/error-card';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { getDatasetPreview, getFileType } from '@/lib/client-side-api';
import type { components } from '@/lib/api/v1';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { LoaderCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MultiSelect } from '@/components/multiselect';

type DatasetPreviewResponse = components['schemas']['PreviewDatasetResponse'];
type FileType = components['schemas']['FileType'];

const sanitize = (value: any) => {
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value);
  } else if (typeof value === 'number') {
    if (isInteger(value)) {
      return String(value);
    } else {
      return (value as number).toFixed(8);
    }
  } else {
    return String(value);
  }
};

const ellipsize = (value: any) => {
  let ellipsizedValue: string = '';
  if (typeof value === 'object' && value !== null) {
    ellipsizedValue = JSON.stringify(value);
  } else if (typeof value === 'number') {
    if (!isInteger(value)) {
      return (value as number).toFixed(2);
    }
  } else {
    ellipsizedValue = String(value);
  }
  if (ellipsizedValue.length > 50) {
    return ellipsizedValue.slice(0, 50) + '...';
  }
  return ellipsizedValue;
};

function FileCell({ url, sample }: { url: string; sample: any }) {
  const [loading, setLoading] = useState<boolean>(true);
  const [contentLoading, setContentLoading] = useState<boolean>(true);
  const [fileType, setFileType] = useState<FileType | null>(null);

  useEffect(() => {
    setLoading(true);
    getFileType(url).then((r) => {
      setFileType(r);
      setLoading(false);
    });
  }, [url]);

  if (loading) {
    return <Skeleton className="w-full h-[64px]" />;
  }

  if (!fileType) {
    return <div>{url}</div>;
  }

  const src = `/api/files?file_url=${url}`;

  if (fileType.image) {
    return (
      <div>
        <Skeleton
          className={`w-full h-[64px] ${contentLoading ? 'block' : 'hidden'}`}
        />
        <img
          src={src}
          className={`h-[64px] ${contentLoading ? 'hidden' : 'block'}`}
          onLoad={() => setContentLoading(false)}
        />
      </div>
    );
  } else if (fileType.video) {
    return (
      <Dialog>
        <DialogTrigger asChild>
          <div>
            <Skeleton
              className={`w-full h-[64px] ${contentLoading ? 'block' : 'hidden'}`}
            />
            <video
              src={src}
              className={`h-[64px] ${contentLoading ? 'hidden' : 'block'}`}
              onCanPlay={() => setContentLoading(false)}
              autoPlay
              muted
              loop
              playsInline
            />
          </div>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Video Preview</DialogTitle>
            <DialogDescription className="w-full break-all">
              {url}
            </DialogDescription>
          </DialogHeader>
          <div className="w-full flex justify-center">
            <video src={src} controls autoPlay className="w-[400px]" />
          </div>
          <DialogFooter className="max-h-[500px] overflow-x-auto overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Key</TableHead>
                  <TableHead>Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.keys(sample).map((key) => (
                  <TableRow key={key}>
                    <TableCell>{key}</TableCell>
                    <TableCell>{sanitize(sample[key])}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  } else {
    return <div>{url}</div>;
  }
}

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
  const [fileColumns, setFileColumns] = useState<string[]>([]);
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
        setFileColumns(
          r.columns
            .filter((column) =>
              r.samples
                .map((s) => s[column.name])
                .every(
                  (v) =>
                    typeof v === 'string' &&
                    (v.startsWith('http://') ||
                      v.startsWith('https://') ||
                      v.startsWith('s3://') ||
                      v.startsWith('hf://') ||
                      v.startsWith('file://'))
                )
            )
            .map((column) => column.name)
        );
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
        <Table>
          <TableHeader>
            <TableRow>
              {columns
                .filter((c) => c.selected)
                .map((column) => (
                  <TableHead key={column.name}>{column.name}</TableHead>
                ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {preview.samples.map((sample, index) => (
              <TableRow key={`preview-sample-${index}`}>
                {columns
                  .filter((c) => c.selected)
                  .map((column) => {
                    const value = sample[column.name];
                    if (fileColumns.includes(column.name)) {
                      return (
                        <TableCell key={column.name}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <FileCell url={value as string} sample={sample} />
                            </TooltipTrigger>
                            <TooltipContent className="w-auto max-w-[500px] text-wrap break-all">
                              {value as string}
                            </TooltipContent>
                          </Tooltip>
                        </TableCell>
                      );
                    }

                    const sanitizedValue = sanitize(value);
                    const ellipsizedValue = ellipsize(sanitizedValue);

                    return (
                      <TableCell key={column.name}>
                        {ellipsizedValue ? (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div>{ellipsizedValue}</div>
                            </TooltipTrigger>
                            <TooltipContent className="w-auto max-w-[500px] text-wrap break-all">
                              {sanitizedValue}
                            </TooltipContent>
                          </Tooltip>
                        ) : (
                          <div>{sanitizedValue}</div>
                        )}
                      </TableCell>
                    );
                  })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
      <CardFooter className="w-full flex justify-center">
        <Pagination
          buttonCount={10}
          totalPages={totalPages}
          currentPage={currentPage}
          pageHref={(page) =>
            `/datasets/${dataset_id}/preview?preview_page=${page}`
          }
        />
      </CardFooter>
    </Card>
  );
}
