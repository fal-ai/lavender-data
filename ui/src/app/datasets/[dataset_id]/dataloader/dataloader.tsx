'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Factory,
  Filter,
  Tag,
  Trash,
  Package,
  Settings,
  Loader2,
  Play,
  ArrowDown,
} from 'lucide-react';
import { useParams } from 'next/navigation';
import type { components } from '@/lib/api/v1';
import {
  createIteration,
  getIterationNextPreview,
} from '@/lib/client-side-api';
import { MultiSelect, MultiSelectItem } from '@/components/multiselect';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { CodeBlock } from '@/components/code-block';
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import SamplesTable from '../samples-table';

type FuncSpec = components['schemas']['FuncSpec'];

const pyTypeToInputType: Record<string, string> = {
  int: 'number',
  float: 'number',
  str: 'text',
  bool: 'checkbox',
  list: 'text',
};

const pyTypeToJsonValue = (type: string, value: string) => {
  if (type === 'bool') {
    return value === 'True';
  } else if (type === 'int') {
    return parseInt(value);
  } else if (type === 'float') {
    return parseFloat(value);
  } else if (type === 'str') {
    return value;
  } else if (type === 'list') {
    return value.split(',');
  } else if (type === 'dict') {
    try {
      return JSON.parse(value);
    } catch (e) {
      return {};
    }
  } else {
    return value;
  }
};

const pyTypeToInputValue = (type: string, value: string) => {
  if (type === 'bool') {
    return value;
  } else if (type === 'int') {
    return value;
  } else if (type === 'float') {
    return value;
  } else if (type === 'str') {
    return `"${value}"`;
  } else if (type === 'list') {
    return `[${value
      .split(',')
      .map((v) => `"${v}"`)
      .join(', ')}]`;
  } else if (type === 'dict') {
    // handle None
    return value;
  } else {
    return value;
  }
};

const specsToMultiSelectItems = (specs: FuncSpec[]) => {
  return specs.map((spec) => ({
    label: spec.name,
    value: spec.name,
    selected: false,
  }));
};

type ArgsState = {
  [name: string]: { [key: string]: { type: string; value: string } };
};

const specToArgsState = (spec: FuncSpec) => {
  return spec.args.reduce(
    (acc: Record<string, { type: string; value: string }>, [key, type]) => {
      acc[key] = {
        type,
        value: '',
      };
      return acc;
    },
    {}
  );
};

const specsToArgsState = (specs: FuncSpec[]) => {
  return specs.reduce((acc: ArgsState, spec) => {
    acc[spec.name] = specToArgsState(spec);
    return acc;
  }, {});
};

const anyArgsDefined = (argsState: ArgsState[string]) => {
  return Object.values(argsState).some(({ value }) => value !== '');
};

const argsPlaceholder = (type: string) => {
  if (type === 'bool') {
    return '';
  } else if (type === 'int') {
    return '1';
  } else if (type === 'float') {
    return '1.0';
  } else if (type === 'str') {
    return 'text';
  } else if (type === 'list') {
    return 'abc, def, ...';
  } else if (type === 'dict') {
    return '{"k": "v", ...} (JSON)';
  } else {
    return '';
  }
};

function SpecParamsInput({
  spec,
  argsState,
  onArgsStateChange,
}: {
  spec: FuncSpec;
  argsState: ArgsState;
  onArgsStateChange: (callback: (argsState: ArgsState) => ArgsState) => void;
}) {
  return (
    <div key={spec.name} className="flex flex-col gap-2">
      <div className="grid grid-cols-[1fr_3fr] items-center gap-4">
        <Badge variant="outline">{spec.name}</Badge>
        <div>
          {spec.args.map(([key, type]) => (
            <div className="grid grid-cols-4 items-center gap-4" key={key}>
              <Label htmlFor="name" className="text-right text-xs font-mono">
                {key}: {type}
              </Label>
              <Input
                className={`col-span-3 ${type === 'bool' ? 'h-6 my-2' : ''}`}
                type={pyTypeToInputType[type]}
                value={argsState[spec.name]?.[key]?.value || ''}
                placeholder={argsPlaceholder(type)}
                onChange={(e) =>
                  onArgsStateChange((prev) => ({
                    ...prev,
                    [spec.name]: {
                      ...prev[spec.name],
                      [key]: {
                        type,
                        value:
                          type === 'bool'
                            ? e.target.checked
                              ? 'True'
                              : 'False'
                            : e.target.value,
                      },
                    },
                  }))
                }
              />
            </div>
          ))}
        </div>
      </div>
      {spec.args.length > 0 && (
        <div className="w-full flex justify-end">
          <Button
            variant="destructive"
            size="sm"
            onClick={() =>
              onArgsStateChange((prev) => ({
                ...prev,
                [spec.name]: specToArgsState(spec),
              }))
            }
          >
            <Trash className="h-4 w-4" />
            Reset
          </Button>
        </div>
      )}
    </div>
  );
}

function FuncInputDialog({
  icon,
  label,
  specs,
  selected,
  setSelected,
  argsState,
  onArgsStateChange,
  singleSelect = false,
}: {
  icon: React.ReactNode;
  label: string;
  specs: FuncSpec[];
  selected: MultiSelectItem[];
  setSelected: (selected: MultiSelectItem[]) => void;
  argsState: ArgsState;
  onArgsStateChange: (callback: (argsState: ArgsState) => ArgsState) => void;
  singleSelect?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          {icon}
          {label}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>{label}</DialogTitle>
        <div className="flex flex-col gap-2">
          <MultiSelect
            className="col-span-3"
            value={selected}
            onChange={setSelected}
            label={label}
            singleSelect={singleSelect}
          />
          {selected
            .filter(({ selected }) => selected)
            .map(({ value }) => specs.find((f) => f.name === value))
            .map(
              (spec) =>
                spec && (
                  <SpecParamsInput
                    key={spec.name}
                    spec={spec}
                    argsState={argsState}
                    onArgsStateChange={onArgsStateChange}
                  />
                )
            )}
          <DialogFooter className="justify-end">
            <Button onClick={() => setOpen(false)}>Save</Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

const argsStateToParams = (argsState: ArgsState[string]) => {
  return Object.entries(argsState)
    .filter(([_, { value }]) => value !== '')
    .reduce((acc: Record<string, any>, [key, { value, type }]) => {
      acc[key] = pyTypeToJsonValue(type, value);
      return acc;
    }, {});
};

const getPipelineParams = (
  selectItems: MultiSelectItem[],
  argsState: ArgsState
) => {
  return selectItems
    .filter(({ selected }) => selected)
    .map(({ value }) => ({
      name: value,
      params: argsStateToParams(argsState[value]),
    }));
};

const argsStateToParamsString = (argsState: ArgsState[string]) => {
  if (!anyArgsDefined(argsState)) {
    return '';
  }
  return Object.entries(argsState)
    .filter(([_, { value }]) => value !== '')
    .map(([key, { value, type }]) => {
      return `"${key}": ${pyTypeToInputValue(type, value)}`;
    })
    .join(', ');
};

const getPipelineParamsStrings = (
  selectItems: MultiSelectItem[],
  argsState: ArgsState
) => {
  return selectItems
    .filter(({ selected }) => selected)
    .map(({ value }) => {
      const args = argsStateToParamsString(argsState[value]);
      if (args) {
        return `("${value}", {${args}})`;
      }
      return `"${value}"`;
    });
};

export function Dataloader({
  apiUrl,
  apiKey,
  shardsetOptions,
  filters,
  categorizers,
  collaters,
  preprocessors,
}: {
  apiUrl: string;
  apiKey?: string;
  shardsetOptions: MultiSelectItem[];
  filters: FuncSpec[];
  categorizers: FuncSpec[];
  collaters: FuncSpec[];
  preprocessors: FuncSpec[];
}) {
  const { dataset_id } = useParams() as { dataset_id: string };

  const [selectedFilters, setFilters] = useState<MultiSelectItem[]>([]);
  const [selectedFiltersArgs, setFiltersArgs] = useState<ArgsState>({});
  const [selectedCategorizers, setCategorizers] = useState<MultiSelectItem[]>(
    []
  );
  const [selectedCategorizersArgs, setCategorizersArgs] = useState<ArgsState>(
    {}
  );
  const [selectedPreprocessors, setPreprocessors] = useState<MultiSelectItem[]>(
    []
  );
  const [selectedPreprocessorsArgs, setPreprocessorsArgs] = useState<ArgsState>(
    {}
  );
  const [selectedCollaters, setCollaters] = useState<MultiSelectItem[]>([]);
  const [selectedCollatersArgs, setCollatersArgs] = useState<ArgsState>({});

  const [shardsets, setShardsets] = useState<MultiSelectItem[]>([]);
  const [maxRetryCount, setMaxRetryCount] = useState<number>(0);
  const [skipOnFailure, setSkipOnFailure] = useState<boolean>(false);
  const [shuffle, setShuffle] = useState<boolean>(false);
  const [shuffleSeed, setShuffleSeed] = useState<number>(0);
  const [shuffleBlockSize, setShuffleBlockSize] = useState<number>(5);
  const [batchSize, setBatchSize] = useState<number>(0);
  const [noCache, setNoCache] = useState<boolean>(false);

  const [samples, setSamples] = useState<any[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [iterationId, setIterationId] = useState<string | null>(null);
  const numSamplesPerFetch = 10;

  useEffect(() => {
    setShardsets(shardsetOptions);
    setFilters(specsToMultiSelectItems(filters));
    setFiltersArgs(specsToArgsState(filters));
    setCategorizers(specsToMultiSelectItems(categorizers));
    setCategorizersArgs(specsToArgsState(categorizers));
    setCollaters(specsToMultiSelectItems(collaters));
    setCollatersArgs(specsToArgsState(collaters));
    setPreprocessors(specsToMultiSelectItems(preprocessors));
    setPreprocessorsArgs(specsToArgsState(preprocessors));
  }, [shardsetOptions, filters, categorizers, collaters, preprocessors]);

  const dataloaderParams = useMemo(() => {
    const params: Record<string, any> = {};
    if (shardsets.filter((s) => s.selected).length > 0) {
      params.shardsets = shardsets
        .filter((s) => s.selected)
        .map((s) => s.value);
    }

    const filters = selectedFilters.filter((f) => f.selected);
    if (filters.length > 0) {
      params.filters = getPipelineParams(filters, selectedFiltersArgs);
    }
    const categorizers = selectedCategorizers.filter((c) => c.selected);
    if (categorizers.length > 0) {
      params.categorizer = getPipelineParams(
        categorizers,
        selectedCategorizersArgs
      )[0];
    }
    const collaters = selectedCollaters.filter((c) => c.selected);
    if (collaters.length > 0) {
      params.collater = getPipelineParams(collaters, selectedCollatersArgs)[0];
    }
    const preprocessors = selectedPreprocessors.filter((p) => p.selected);
    if (preprocessors.length > 0) {
      params.preprocessors = getPipelineParams(
        preprocessors,
        selectedPreprocessorsArgs
      );
    }

    if (maxRetryCount > 0) {
      params.max_retry_count = `${maxRetryCount}`;
    }
    if (skipOnFailure) {
      params.skip_on_failure = skipOnFailure ? 'True' : 'False';
    }
    if (shuffle) {
      params.shuffle = shuffle ? 'True' : 'False';
      params.shuffle_block_size = `${shuffleBlockSize}`;
    }
    if (shuffleSeed) {
      params.shuffle_seed = `${shuffleSeed}`;
    }
    if (batchSize) {
      params.batch_size = `${batchSize}`;
    }
    if (noCache) {
      params.no_cache = noCache ? 'True' : 'False';
    }

    return params;
  }, [
    shardsets,
    selectedFilters,
    selectedFiltersArgs,
    selectedCategorizers,
    selectedCategorizersArgs,
    selectedCollaters,
    selectedCollatersArgs,
    selectedPreprocessors,
    selectedPreprocessorsArgs,
    maxRetryCount,
    skipOnFailure,
    shuffle,
    shuffleSeed,
    shuffleBlockSize,
    batchSize,
    noCache,
  ]);

  const dataloaderParamsString = useMemo(() => {
    // TODO get it from dataloaderParams

    const params: Record<string, string> = {};
    if (shardsets.filter((s) => s.selected).length > 0) {
      params.shardsets =
        '[' +
        shardsets
          .filter((s) => s.selected)
          .map((s) => `"${s.value}"`)
          .join(', ') +
        ']';
    }

    const filters = selectedFilters.filter((f) => f.selected);
    if (filters.length > 0) {
      params.filters =
        '[' +
        getPipelineParamsStrings(filters, selectedFiltersArgs).join(', ') +
        ']';
    }
    const categorizers = selectedCategorizers.filter((c) => c.selected);
    if (categorizers.length > 0) {
      params.categorizer = getPipelineParamsStrings(
        categorizers,
        selectedCategorizersArgs
      )[0];
    }
    const collaters = selectedCollaters.filter((c) => c.selected);
    if (collaters.length > 0) {
      params.collater = getPipelineParamsStrings(
        collaters,
        selectedCollatersArgs
      )[0];
    }
    const preprocessors = selectedPreprocessors.filter((p) => p.selected);
    if (preprocessors.length > 0) {
      params.preprocessors =
        '[' +
        getPipelineParamsStrings(preprocessors, selectedPreprocessorsArgs).join(
          ', '
        ) +
        ']';
    }

    if (maxRetryCount > 0) {
      params.max_retry_count = `${maxRetryCount}`;
    }
    if (skipOnFailure) {
      params.skip_on_failure = skipOnFailure ? 'True' : 'False';
    }
    if (shuffle) {
      params.shuffle = shuffle ? 'True' : 'False';
      params.shuffle_block_size = `${shuffleBlockSize}`;
    }
    if (shuffleSeed) {
      params.shuffle_seed = `${shuffleSeed}`;
    }
    if (batchSize) {
      params.batch_size = `${batchSize}`;
    }
    if (noCache) {
      params.no_cache = noCache ? 'True' : 'False';
    }

    return Object.entries(params)
      .map(([key, value]) => `\n    ${key}=${value},`)
      .join('');
  }, [
    shardsets,
    selectedFilters,
    selectedFiltersArgs,
    selectedCategorizers,
    selectedCategorizersArgs,
    selectedCollaters,
    selectedCollatersArgs,
    selectedPreprocessors,
    selectedPreprocessorsArgs,
    maxRetryCount,
    skipOnFailure,
    shuffle,
    shuffleSeed,
    shuffleBlockSize,
    batchSize,
    noCache,
  ]);

  const onStartIteration = useCallback(async () => {
    setLoading(true);
    setSamples([]);
    setColumns([]);
    const iteration = await createIteration(dataset_id, dataloaderParams);
    setIterationId(iteration.id);
    setLoading(false);

    onLoadMore(iteration.id);
  }, [dataloaderParams]);

  const onLoadMore = useCallback(async (iterationId: string) => {
    setLoading(true);
    const samples = (
      await Promise.allSettled(
        Array.from({ length: numSamplesPerFetch }).map(() =>
          getIterationNextPreview(iterationId)
        )
      )
    )
      .filter((s) => s.status === 'fulfilled')
      .map((s) => s.value);
    setSamples((prev) => [...prev, ...samples]);
    setColumns(Object.keys(samples[0]));
    setLoading(false);
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <Card className="w-full">
        <CardContent>
          <div className="flex flex-col gap-2 max-w-[640px] mb-8">
            <div className="grid grid-cols-4 gap-2">
              <Label>Shardsets</Label>
              <MultiSelect
                value={shardsets}
                onChange={setShardsets}
                label="Select shardsets"
                className="col-span-3 w-full"
              />
            </div>
            <div className="grid grid-cols-4 gap-2">
              <Label>Pipelines</Label>
              <div className="flex gap-2 col-span-3">
                <FuncInputDialog
                  icon={<Filter className="h-4 w-4" />}
                  label="Filters"
                  specs={filters}
                  selected={selectedFilters}
                  setSelected={setFilters}
                  argsState={selectedFiltersArgs}
                  onArgsStateChange={setFiltersArgs}
                />
                <FuncInputDialog
                  icon={<Tag className="h-4 w-4" />}
                  label="Categorizer"
                  specs={categorizers}
                  selected={selectedCategorizers}
                  setSelected={setCategorizers}
                  argsState={selectedCategorizersArgs}
                  onArgsStateChange={setCategorizersArgs}
                  singleSelect={true}
                />
                <FuncInputDialog
                  icon={<Package className="h-4 w-4" />}
                  label="Collater"
                  specs={collaters}
                  selected={selectedCollaters}
                  setSelected={setCollaters}
                  argsState={selectedCollatersArgs}
                  onArgsStateChange={setCollatersArgs}
                  singleSelect={true}
                />
                <FuncInputDialog
                  icon={<Factory className="h-4 w-4" />}
                  label="Preprocessors"
                  specs={preprocessors}
                  selected={selectedPreprocessors}
                  setSelected={setPreprocessors}
                  argsState={selectedPreprocessorsArgs}
                  onArgsStateChange={setPreprocessorsArgs}
                />
              </div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <Label>Shuffle</Label>
              <div className="col-span-3 w-full flex items-center gap-4">
                <Switch checked={shuffle} onCheckedChange={setShuffle} />
                <div className="flex gap-2">
                  <Label
                    htmlFor="shuffle-block-size"
                    className={`text-right ${
                      shuffle ? '' : 'text-muted-foreground'
                    }`}
                  >
                    Block Size
                  </Label>
                  <Input
                    id="shuffle-block-size"
                    type="number"
                    value={shuffleBlockSize}
                    onChange={(e) =>
                      setShuffleBlockSize(parseInt(e.target.value) || 0)
                    }
                    min={1}
                    disabled={!shuffle}
                  />
                </div>
                <div className="flex gap-2">
                  <Label
                    htmlFor="shuffle-seed"
                    className={`text-right ${
                      shuffle ? '' : 'text-muted-foreground'
                    }`}
                  >
                    Seed
                  </Label>
                  <Input
                    id="shuffle-seed"
                    type="number"
                    value={shuffleSeed}
                    onChange={(e) =>
                      setShuffleSeed(parseInt(e.target.value) || 0)
                    }
                    disabled={!shuffle}
                  />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <Label>Settings</Label>
              <div className="col-span-3">
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <Settings className="h-4 w-4" />
                      Settings
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogTitle>Settings</DialogTitle>
                    <div className="grid grid-cols-4 gap-2">
                      <Label>Batch Size</Label>
                      <Input
                        min={0}
                        type="number"
                        value={batchSize}
                        onChange={(e) =>
                          setBatchSize(parseInt(e.target.value) || 0)
                        }
                      />
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                      <Label>Max Retry Count</Label>
                      <Input
                        min={0}
                        type="number"
                        value={maxRetryCount}
                        onChange={(e) =>
                          setMaxRetryCount(parseInt(e.target.value) || 0)
                        }
                      />
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                      <Label>Skip On Failure</Label>
                      <Switch
                        checked={skipOnFailure}
                        onCheckedChange={setSkipOnFailure}
                      />
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                      <Label>No Cache</Label>
                      <Switch checked={noCache} onCheckedChange={setNoCache} />
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
          <CodeBlock
            className="text-sm"
            language="python"
            code={`
import lavender_data.client as lavender

lavender.init(
    api_url="${apiUrl}",${
      apiKey
        ? `
    api_key="${apiKey}",`
        : ''
    }
)

dataloader = lavender.LavenderDataLoader(
    "${dataset_id}",${dataloaderParamsString}
)`}
          />
        </CardContent>
        <CardFooter>
          <Button onClick={onStartIteration} disabled={loading}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Start Iteration
          </Button>
        </CardFooter>
      </Card>
      <Card>
        <CardContent>
          <SamplesTable samples={samples} columns={columns} />
        </CardContent>
        <CardFooter>
          {samples.length > 0 && (
            <Button
              onClick={() => iterationId && onLoadMore(iterationId)}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowDown className="h-4 w-4" />
              )}
              Load More
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
