'use client';

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { components } from '@/lib/api/v1';

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
  const random = Math.random();

  let has_lower_outlier = false;
  let has_upper_outlier = false;

  if (histogram.bin_edges.length > 3) {
    const gap = histogram.bin_edges[2] - histogram.bin_edges[1];
    if (histogram.bin_edges[1] - histogram.bin_edges[0] > gap) {
      has_lower_outlier = true;
    }
    if (
      histogram.bin_edges[histogram.bin_edges.length - 1] -
        histogram.bin_edges[histogram.bin_edges.length - 2] >
      gap
    ) {
      has_upper_outlier = true;
    }
  }

  const isOutlier = (index: number) => {
    if (has_lower_outlier && index === 0) {
      return true;
    }
    if (has_upper_outlier && index === histogram.hist.length - 1) {
      return true;
    }
    return false;
  };

  return (
    <div
      className="pt-1 flex flex-col items-start justify-start h-full"
      style={{ width: `${width}px` }}
    >
      <svg width={width} height={svgHeight}>
        <g>
          {histogram.hist.map((h, i) => (
            <Tooltip key={`histogram-${columnName}-${random}-${i}`}>
              <rect
                className="fill-gray-400 dark:fill-gray-500/80"
                rx="2"
                x={i * (width / histogram.hist.length)}
                y={svgHeight - (h / hMax) * svgHeight}
                width={width / histogram.hist.length - 2}
                height={(h / hMax) * svgHeight}
                fillOpacity={isOutlier(i) ? 0.3 : 1}
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
                <div>{isOutlier(i) ? '[Outlier]' : ''}</div>
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
      <div className="flex flex-col w-full text-xs font-mono font-light text-muted-foreground">
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
  const random = Math.random();
  return (
    <div
      className="pt-1 flex flex-col items-start justify-start h-full"
      style={{ width: `${width}px` }}
    >
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
              <Tooltip key={`histogram-${columnName}-${random}-${i}`}>
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
                    {((count / hMax) * 100).toFixed(2)}% ({formatNumber(count)})
                  </div>
                </TooltipContent>
              </Tooltip>
            ))}
          </g>
        </svg>
      )}
      <div className="flex flex-col w-full text-xs font-mono font-light text-muted-foreground">
        <div className={`flex justify-between w-full`}>
          <div>{formatNumber(n_unique)} values</div>
        </div>
        <div className="w-full h-[1px] bg-gray-200 dark:bg-gray-500/20"></div>
      </div>
    </div>
  );
}

export function StatisticsCell({
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
  return <div>-</div>;
}
