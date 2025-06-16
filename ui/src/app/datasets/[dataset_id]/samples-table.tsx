'use client';

import { isInteger } from 'lodash';
import { useState, useEffect, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { inspectFileType, getFileType } from '@/lib/client-side-api';
import type { components } from '@/lib/api/v1';
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
import { Button } from '@/components/ui/button';
import { Eye } from 'lucide-react';

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

function FileCell({
  defaultShow,
  url,
  sample,
}: {
  defaultShow: boolean;
  url: string;
  sample: any;
}) {
  const [show, setShow] = useState<boolean>(defaultShow);
  const [loading, setLoading] = useState<boolean>(true);
  const [contentLoading, setContentLoading] = useState<boolean>(true);

  const [fileType, setFileType] = useState<FileType | null>(null);
  const [fileTypePollCount, setFileTypePollCount] = useState<number>(0);

  useEffect(() => {
    setShow(defaultShow);
    setLoading(true);
    setFileTypePollCount(0);
    inspectFileType(url).then((r) => {
      setFileTypePollCount(fileTypePollCount + 1);
    });
  }, [url]);

  useEffect(() => {
    if (fileTypePollCount > 0) {
      getFileType(url)
        .then((r) => {
          setFileType(r);
          setLoading(false);
        })
        .catch((e) => {
          if (e.message.includes('400')) {
            setTimeout(() => setFileTypePollCount(fileTypePollCount + 1), 100);
          } else {
            setLoading(false);
          }
        });
    }
  }, [url, fileTypePollCount]);

  if (loading) {
    return <Skeleton className="w-full h-[64px]" />;
  }

  if (!fileType) {
    return <div>{url}</div>;
  }

  const src = `/api/static?file_url=${url}`;

  if (fileType.image) {
    return (
      <Dialog>
        <DialogTrigger asChild>
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
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Image Preview</DialogTitle>
            <DialogDescription className="w-full break-all">
              {url}
            </DialogDescription>
          </DialogHeader>
          <div className="w-full flex justify-center">
            <img src={src} className="w-[400px]" />
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
  } else if (fileType.video) {
    return (
      <Dialog>
        <DialogTrigger asChild>
          {show ? (
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
          ) : (
            <Button className="w-full h-[64px]" onClick={() => setShow(true)}>
              <Eye />
            </Button>
          )}
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

export default function SamplesTable({
  samples,
  columns,
}: {
  samples: any[];
  columns: string[];
}) {
  const fileColumns = useMemo(
    () =>
      columns
        .filter((column) =>
          samples
            .map((s) => s[column])
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
        .map((column) => column),
    [samples, columns]
  );

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead key={column}>{column}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {samples.map((sample, index) => (
          <TableRow key={`preview-sample-${index}`}>
            {columns.map((column) => {
              const value = sample[column];
              if (fileColumns.includes(column)) {
                return (
                  <TableCell key={column}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <FileCell
                          defaultShow={false}
                          url={value as string}
                          sample={sample}
                        />
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
                <TableCell key={column}>
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
  );
}
