'use client';

import { BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { StatisticsCell } from '../../statistics-cell';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { getShardStatistics, ShardStatistics } from '@/lib/client-side-api';
import { useEffect, useState } from 'react';
import Loading from '../../loading';

export function ShardStatisticsDialog({
  dataset_id,
  shardset_id,
  shard_id,
  shard_location,
}: {
  dataset_id: string;
  shardset_id: string;
  shard_id: string;
  shard_location: string;
}) {
  const [open, setOpen] = useState(false);
  const [statistics, setStatistics] = useState<ShardStatistics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      getShardStatistics(dataset_id, shardset_id, shard_id)
        .then(setStatistics)
        .catch((error) => setError(error.message));
    }
  }, [dataset_id, shardset_id, shard_id, open]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon">
          <BarChart3 className="w-4 h-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>{shard_location}</DialogTitle>
          <DialogDescription>{shard_id}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-wrap gap-2 gap-y-8 w-full">
          {statistics ? (
            Object.entries(statistics.data)
              .sort((a, b) => a[0].localeCompare(b[0]))
              .map(([columnName, value]) => (
                <div key={`${shard_location}-${columnName}`}>
                  <div className="text-xs font-mono">{columnName}</div>
                  <StatisticsCell
                    columnName={columnName}
                    statistics={
                      value.type === 'numeric'
                        ? {
                            type: 'numeric',
                            histogram: value.histogram,
                            nan_count: value.nan_count,
                            max: value.max,
                            min: value.min,
                            mean: value.sum / value.count,
                            median: value.median,
                            std: Math.sqrt(
                              value.sum_squared / value.count -
                                (value.sum / value.count) ** 2
                            ),
                          }
                        : value
                    }
                  />
                </div>
              ))
          ) : error ? (
            <div>{error}</div>
          ) : (
            <div>
              <Loading />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
