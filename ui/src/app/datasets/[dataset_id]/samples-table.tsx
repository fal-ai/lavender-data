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
import { Eye, EyeClosed } from 'lucide-react';
import { MultiSelect } from '@/components/multiselect';
import mime from 'mime-types';
import { Switch } from '@/components/ui/switch';
import type { components } from '@/lib/api/v1';

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

const getFileType = (url: string) => {
  const mimeType = mime.lookup(url.split('?')[0]);
  if (!mimeType) {
    return {
      image: false,
      video: false,
    };
  }
  return {
    image: mimeType.startsWith('image/'),
    video: mimeType.startsWith('video/') || mimeType == 'application/mp4',
  };
};

const getFileUrl = (url: string) => {
  if (url.startsWith('file://')) {
    const filename = url.replace('file://', '');
    return `/api/files/${filename}`;
  }
  return url;
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
  const [contentLoading, setContentLoading] = useState<boolean>(true);

  useEffect(() => {
    setShow(defaultShow);
    setContentLoading(true);
  }, [url]);

  useEffect(() => {
    setShow(defaultShow);
  }, [defaultShow]);

  const src = getFileUrl(url);
  const fileType = getFileType(url);

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

const formatFloat = (value: number) => {
  if (value.toFixed(2).endsWith('00')) {
    return value.toFixed(0);
  }
  return value.toFixed(2);
};

const formatNumber = (value: number) => {
  if (value < 1000) {
    return `${formatFloat(value)}`;
  } else if (value < 1000 * 1000) {
    return `${formatFloat(value / 1000)}k`;
  } else if (value < 1000 * 1000 * 1000) {
    return `${formatFloat(value / 1000 / 1000)}m`;
  } else if (value < 1000 * 1000 * 1000 * 1000) {
    return `${formatFloat(value / 1000 / 1000 / 1000)}g`;
  } else {
    return `${formatFloat(value / 1000 / 1000 / 1000 / 1000)}t`;
  }
};

function NumericStatisticsCell({
  columnName,
  statistics,
}: {
  columnName: string;
  statistics: components['schemas']['NumericColumnStatistics'];
}) {
  const width = 132;
  const svgHeight = 40;
  const { max, min, mean, median, std, histogram } = statistics;
  const count = histogram.hist.reduce((acc, h) => acc + h, 0);
  const hMax = Math.max(...histogram.hist);
  return (
    <div className={`pt-1 flex flex-col items-start justify-start h-full`}>
      <svg width={width} height={svgHeight}>
        <g>
          {histogram.hist.map((h, i) => (
            <Tooltip key={`histogram-${columnName}-${i}`}>
              <rect
                className="fill-gray-400 dark:fill-gray-500/80"
                rx="2"
                x={i * (width / histogram.hist.length)}
                y={svgHeight - (h / hMax) * svgHeight}
                width={width / histogram.hist.length - 2}
                height={(h / hMax) * svgHeight}
                fillOpacity="1"
              ></rect>
              <TooltipTrigger asChild>
                <rect
                  rx="2"
                  x={i * (width / histogram.hist.length)}
                  y={svgHeight - svgHeight}
                  width={width / histogram.hist.length - 2}
                  height={svgHeight}
                  fillOpacity="0"
                ></rect>
              </TooltipTrigger>
              <TooltipContent className="w-auto text-wrap break-all font-mono">
                <div>
                  {formatNumber(histogram.bin_edges[i])} -{' '}
                  {formatNumber(histogram.bin_edges[i + 1])}
                </div>
                <div>
                  {((h / count) * 100).toFixed(2)}% ({formatNumber(h)})
                </div>
              </TooltipContent>
            </Tooltip>
          ))}
        </g>
      </svg>
      <div
        className={`flex flex-col w-[${width}px] text-xs font-mono font-light text-muted-foreground`}
      >
        <div className={`flex justify-between w-full`}>
          <div>{formatNumber(min)}</div>
          <div>{formatNumber(max)}</div>
        </div>
        <div className="w-full h-[1px] bg-gray-200 dark:bg-gray-500/20"></div>
        <div className={`flex justify-between w-full`}>
          <div>Mean</div>
          <div>{formatNumber(mean)}</div>
        </div>
        <div className={`flex justify-between w-full`}>
          <div>Std</div>
          <div>{formatNumber(std)}</div>
        </div>
        <div className={`flex justify-between w-full`}>
          <div>Median</div>
          <div>{formatNumber(median)}</div>
        </div>
      </div>
    </div>
  );
}

function CategoricalStatisticsCell({
  columnName,
  statistics,
}: {
  columnName: string;
  statistics: components['schemas']['CategoricalColumnStatistics'];
}) {
  const width = 132;
  const svgHeight = 40;
  const { frequencies, n_unique } = statistics;
  const hideHistogram = Object.keys(frequencies).length > 100;
  const hMax = hideHistogram ? 1 : Math.max(...Object.values(frequencies));
  return (
    <div className={`pt-1 flex flex-col items-start justify-start h-full`}>
      {hideHistogram ? (
        <div
          className={`w-[${width}px] h-[${svgHeight}px] flex items-center justify-center text-xs font-mono font-light text-muted-foreground`}
        >
          (redacted)
        </div>
      ) : (
        <svg width={width} height={svgHeight}>
          <g>
            {Object.entries(frequencies).map(([value, count], i) => (
              <Tooltip key={`histogram-${columnName}-${i}`}>
                <rect
                  className="fill-gray-400 dark:fill-gray-500/80"
                  rx="2"
                  x={i * (width / n_unique)}
                  y={svgHeight - (count / hMax) * svgHeight}
                  width={width / n_unique - 2}
                  height={(count / hMax) * svgHeight}
                  fillOpacity="1"
                ></rect>
                <TooltipTrigger asChild>
                  <rect
                    rx="2"
                    x={i * (width / n_unique)}
                    y={svgHeight - svgHeight}
                    width={width / n_unique - 2}
                    height={svgHeight}
                    fillOpacity="0"
                  ></rect>
                </TooltipTrigger>
                <TooltipContent className="w-auto text-wrap break-all font-mono">
                  <div>{value}</div>
                  <div>
                    {((count / n_unique) * 100).toFixed(2)}% (
                    {formatNumber(count)})
                  </div>
                </TooltipContent>
              </Tooltip>
            ))}
          </g>
        </svg>
      )}
      <div
        className={`flex flex-col w-[${width}px] text-xs font-mono font-light text-muted-foreground`}
      >
        <div className={`flex justify-between w-full`}>
          <div>{formatNumber(n_unique)} values</div>
        </div>
        <div className="w-full h-[1px] bg-gray-200 dark:bg-gray-500/20"></div>
      </div>
    </div>
  );
}

function StatisticsCell({
  columnName,
  statistics,
}: {
  columnName: string;
  statistics: components['schemas']['GetDatasetStatisticsResponse']['statistics'][string];
}) {
  if (statistics.type === 'numeric') {
    return (
      <NumericStatisticsCell columnName={columnName} statistics={statistics} />
    );
  } else if (statistics.type === 'categorical') {
    return (
      <CategoricalStatisticsCell
        columnName={columnName}
        statistics={statistics}
      />
    );
  }
  return <div>Unknown</div>;
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

export default function SamplesTable({
  datasetId,
  samples,
  fetchedColumns,
  statistics,
}: {
  datasetId: string;
  samples: any[];
  fetchedColumns: string[];
  statistics?: components['schemas']['GetDatasetStatisticsResponse'];
}) {
  const [defaultShow, setDefaultShow] = useState<boolean>(false);
  const [columns, setColumns] = useState<
    {
      name: string;
      selected: boolean;
    }[]
  >([]);

  useEffect(() => {
    const storedColumns = getColumnsFromLocalStorage(datasetId);

    if (storedColumns.length === 0) {
      setColumns(
        fetchedColumns.map((c) => ({
          name: c,
          selected: true,
        }))
      );
    } else {
      setColumns(storedColumns);
    }
  }, [datasetId, fetchedColumns]);

  useEffect(() => {
    if (columns.length > 0) {
      setColumnsToLocalStorage(datasetId, columns);
    }
  }, [datasetId, columns]);

  const fileColumns = useMemo(
    () =>
      columns
        .filter((column) =>
          samples
            .map((s) => s[column.name])
            .every(
              (v) =>
                typeof v === 'string' &&
                (v.startsWith('http://') ||
                  v.startsWith('https://') ||
                  v.startsWith('file://'))
            )
        )
        .map((column) => column),
    [samples, columns]
  );

  console.log(statistics);

  return (
    <div>
      <div className="w-full flex justify-start items-center mb-4 gap-8">
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
                fetchedColumns.map((name) => ({
                  name,
                  selected: true,
                }))
              )
            }
          >
            Reset
          </Button>
        </div>
        <div className="flex gap-2">
          <EyeClosed className="w-5 h-5" />
          <Switch
            checked={defaultShow}
            onCheckedChange={setDefaultShow}
            aria-label="Default show"
          />
          <Eye className="w-5 h-5" />
        </div>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            {columns
              .filter((column) => column.selected)
              .map((column) => (
                <TableHead key={column.name}>{column.name}</TableHead>
              ))}
          </TableRow>
          {statistics && (
            <TableRow>
              {columns
                .filter((column) => column.selected)
                .map((column) => (
                  <TableHead key={`${column.name}-statistics`}>
                    {statistics.statistics[column.name] ? (
                      <StatisticsCell
                        columnName={column.name}
                        statistics={statistics.statistics[column.name]}
                      />
                    ) : (
                      <div>-</div>
                    )}
                  </TableHead>
                ))}
            </TableRow>
          )}
        </TableHeader>
        <TableBody>
          {samples.map((sample, index) => (
            <TableRow key={`preview-sample-${index}`}>
              {columns
                .filter((column) => column.selected)
                .map((column) => {
                  const value = sample[column.name];
                  if (
                    fileColumns.some(
                      (c) => c.name === column.name && c.selected
                    )
                  ) {
                    return (
                      <TableCell key={column.name}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <FileCell
                              defaultShow={defaultShow}
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
    </div>
  );
}
