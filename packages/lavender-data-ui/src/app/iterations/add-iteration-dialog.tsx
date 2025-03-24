'use client';

import { useState, useEffect, useRef } from 'react';
import { Info, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { useFormStatus } from 'react-dom';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { IconTooltip } from '@/components/icon-tooltip';
import { client } from '@/lib/api';
import { createIteration } from './add-iteration-action';

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" disabled={pending}>
      {pending ? 'Saving...' : 'Save'}
    </Button>
  );
}

export function AddIterationDialog({
  fixedDataset,
  children,
}: {
  fixedDataset?: any;
  children: React.ReactNode;
}) {
  const [datasetId, setDatasetId] = useState(
    fixedDataset ? fixedDataset.id : ''
  );
  const [datasets, setDatasets] = useState<any[]>([]);
  const [dataset, setDataset] = useState<any>(fixedDataset || null);
  const [shardsets, setShardsets] = useState<string[]>([]);

  const [preprocessors, setPreprocessors] = useState<string[]>([]);
  const [filters, setFilters] = useState<string[]>([]);
  const [collaters, setCollaters] = useState<string[]>([]);

  const [preprocessor, setPreprocessor] = useState<string>('');
  const [filter, setFilter] = useState<string>('');
  const [collater, setCollater] = useState<string>('');

  const [shuffle, setShuffle] = useState(false);
  const [shuffleSeed, setShuffleSeed] = useState(0);
  const [shuffleBlockSize, setShuffleBlockSize] = useState(1);
  const [batchSize, setBatchSize] = useState(0);
  const [replicationPg, setReplicationPg] = useState<string>('');

  const [open, setOpen] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    client.GET('/datasets/').then((res) => {
      if (res.error) {
        toast.error(JSON.stringify(res.error));
      } else {
        setDatasets(res.data);
      }
    });
    client.GET('/registries/preprocessors').then((res) => {
      if (!res.data) {
        toast.error('Failed to fetch preprocessors');
      } else {
        setPreprocessors(res.data);
      }
    });
    client.GET('/registries/filters').then((res) => {
      if (!res.data) {
        toast.error('Failed to fetch filters');
      } else {
        setFilters(res.data);
      }
    });
    client.GET('/registries/collaters').then((res) => {
      if (!res.data) {
        toast.error('Failed to fetch collaters');
      } else {
        setCollaters(res.data);
      }
    });
  }, []);

  useEffect(() => {
    if (datasetId) {
      client
        .GET('/datasets/{dataset_id}', {
          params: { path: { dataset_id: datasetId } },
        })
        .then((res) => {
          if (res.error) {
            throw new Error(JSON.stringify(res.error));
          }
          setDataset(res.data);
        });
    }
  }, [datasetId]);

  // Client action wrapper
  const clientAction = async (formData: FormData) => {
    // Add dynamic values to form data
    formData.set('datasetId', datasetId);
    formData.set('shardsetsJson', JSON.stringify(shardsets));
    formData.set('preprocessor', preprocessor);
    formData.set('filter', filter);
    formData.set('collater', collater);
    formData.set('shuffle', shuffle.toString());
    formData.set('shuffleSeed', shuffleSeed.toString());
    formData.set('shuffleBlockSize', shuffleBlockSize.toString());
    formData.set('batchSize', batchSize.toString());
    formData.set('replicationPg', replicationPg);

    const result = await createIteration(formData);

    if (result.success) {
      toast.success('Iteration added successfully');
      setOpen(false);
      formRef.current?.reset();
    } else {
      toast.error(`Failed to add iteration: ${result.error}`);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>New iteration</DialogTitle>
          <DialogDescription>Start a new iteration.</DialogDescription>
        </DialogHeader>
        <form ref={formRef} action={clientAction}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="dataset_id" className="text-right">
                Dataset
              </Label>
              <div className="col-span-3">
                <Select
                  onValueChange={(value) => setDatasetId(value)}
                  value={datasetId}
                  disabled={fixedDataset}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets.map((dataset) => (
                      <SelectItem key={dataset.id} value={dataset.id}>
                        {dataset.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="shardsets" className="text-right">
                Shardsets
                <IconTooltip
                  icon={<Info className="w-4 h-4" />}
                  content={
                    <p>
                      Select the shardsets you want to use for the iteration.
                      <br />
                      If you don't select any shardsets, all shardsets will be
                      used.
                    </p>
                  }
                />
              </Label>
              <div className="col-span-3 flex flex-col gap-2">
                {shardsets.map((shardset, index) => (
                  <div
                    className="grid grid-cols-3 items-center gap-4"
                    key={`shardset-${index}`}
                  >
                    <div className="col-span-2">
                      <Select
                        disabled={!dataset}
                        value={shardsets[index]}
                        onValueChange={(value) =>
                          setShardsets(
                            shardsets.map((s, i) => (i === index ? value : s))
                          )
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select shardset" />
                        </SelectTrigger>
                        <SelectContent>
                          {dataset?.shardsets.map((shardset: any) => (
                            <SelectItem
                              key={shardset.id}
                              value={shardset.id}
                              disabled={shardsets.includes(shardset.id)}
                            >
                              {shardset.location}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-1">
                      <Button
                        type="button"
                        variant="outline"
                        className="w-full"
                        onClick={() =>
                          setShardsets(shardsets.filter((_, i) => i !== index))
                        }
                      >
                        Clear
                      </Button>
                    </div>
                  </div>
                ))}
                {(shardsets.length == 0 ||
                  shardsets.length < dataset?.shardsets.length) && (
                  <Button
                    type="button"
                    disabled={!dataset}
                    variant="outline"
                    onClick={() => setShardsets([...shardsets, ''])}
                  >
                    <Plus />
                    Add shardset
                  </Button>
                )}
              </div>
            </div>
            <Separator />
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="preprocessor" className="text-right">
                Preprocessor
              </Label>
              <div className="col-span-2">
                <Select
                  disabled={!dataset}
                  value={preprocessor}
                  onValueChange={(value) => setPreprocessor(value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select preprocessor" />
                  </SelectTrigger>
                  <SelectContent>
                    {preprocessors.map((preprocessor) => (
                      <SelectItem key={preprocessor} value={preprocessor}>
                        {preprocessor}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-1">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setPreprocessor('')}
                  className="w-full"
                >
                  Clear
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="filter" className="text-right">
                Filter
              </Label>
              <div className="col-span-2">
                <Select
                  disabled={!dataset}
                  value={filter}
                  onValueChange={(value) => setFilter(value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select filter" />
                  </SelectTrigger>
                  <SelectContent>
                    {filters.map((filter) => (
                      <SelectItem key={filter} value={filter}>
                        {filter}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-1">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setFilter('')}
                  className="w-full"
                >
                  Clear
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="collater" className="text-right">
                Collater
              </Label>
              <div className="col-span-2">
                <Select
                  disabled={!dataset}
                  value={collater}
                  onValueChange={(value) => setCollater(value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select collater" />
                  </SelectTrigger>
                  <SelectContent>
                    {collaters.map((collater) => (
                      <SelectItem key={collater} value={collater}>
                        {collater}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-1">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCollater('')}
                  className="w-full"
                >
                  Clear
                </Button>
              </div>
            </div>
            <Separator />
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="shuffle" className="text-right">
                Shuffle
              </Label>
              <Switch
                checked={shuffle}
                onCheckedChange={(value) => setShuffle(value)}
                disabled={!dataset}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="shuffleSeed" className="text-right">
                Seed
              </Label>
              <Input
                id="shuffleSeed"
                type="number"
                value={shuffleSeed}
                onChange={(e) => setShuffleSeed(Number(e.target.value))}
                disabled={!dataset || !shuffle}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="shuffleBlockSize" className="text-right">
                Block size
                <IconTooltip
                  icon={<Info className="w-4 h-4" />}
                  content={
                    <p>
                      The number of shards to shuffle at a time.
                      <br />
                      If you set this to 1, the samples will be shuffled within
                      each shard.
                      <br />
                      Larger block size will provide more randomness, but will
                      also increase the disk usage.
                      <br />
                      Each rank's cache size should be greater than or equal to
                      the block size.
                    </p>
                  }
                />
              </Label>
              <Input
                id="shuffleBlockSize"
                type="number"
                value={shuffleBlockSize}
                min={1}
                onChange={(e) => setShuffleBlockSize(Number(e.target.value))}
                disabled={!dataset || !shuffle}
                className="col-span-3"
              />
            </div>
            <Separator />
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="batchSize" className="text-right">
                Batch size
              </Label>
              <Input
                id="batchSize"
                type="number"
                value={batchSize}
                min={0}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="col-span-3"
                disabled={!dataset}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="replicationPg" className="text-right">
                Replication Pg
                <IconTooltip
                  icon={<Info className="w-4 h-4" />}
                  content={
                    <p>
                      Replication process groups (pg) in JSON format.
                      <br />
                      Each pg should be a list of ranks. (e.g. [[0,1],[2,3]])
                      <br />
                      Each rank in the same pg will get the same samples.
                      <br />
                      This is useful for context parallelism.
                    </p>
                  }
                />
              </Label>
              <Input
                id="replicationPg"
                type="text"
                value={replicationPg}
                placeholder="[[0,1],[2,3]]"
                onChange={(e) => setReplicationPg(e.target.value)}
                className="col-span-3"
                disabled={!dataset}
              />
            </div>
          </div>
          <DialogFooter>
            <SubmitButton />
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
