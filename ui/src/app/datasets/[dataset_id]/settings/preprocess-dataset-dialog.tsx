'use client';

import { useRef, useState } from 'react';
import { Plus, Info } from 'lucide-react';
import { toast } from 'sonner';
import { useFormStatus } from 'react-dom';
import { ScrollArea } from '@/components/ui/scroll-area';
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
import { IconTooltip } from '@/components/icon-tooltip';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { preprocessDataset } from './preprocess-dataset-action';
import { Checkbox } from '@/components/ui/checkbox';

type Shardset = {
  id: string;
  location: string;
};

type Preprocessor = {
  name: string;
  params: string;
};

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" disabled={pending}>
      {pending ? 'Saving...' : 'Save'}
    </Button>
  );
}

function PreprocessorInputs({
  index,
  preprocessors,
  preprocessorInputs,
  setPreprocessorInputs,
}: {
  index: number;
  preprocessors: string[];
  preprocessorInputs: Preprocessor[];
  setPreprocessorInputs: (preprocessorInputs: Preprocessor[]) => void;
}) {
  return (
    <div className="my-4">
      <div className="flex flex-col gap-2">
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor={'preprocessor-name-' + index}>Name</Label>
          <Select
            required
            value={preprocessorInputs[index].name}
            onValueChange={(value) =>
              setPreprocessorInputs(
                preprocessorInputs.map((preprocessor, i) =>
                  i === index ? { ...preprocessor, name: value } : preprocessor
                )
              )
            }
          >
            <SelectTrigger className="col-span-3">
              <SelectValue placeholder="Select a preprocessor" />
            </SelectTrigger>
            <SelectContent className="col-span-3">
              {preprocessors.map((preprocessor) => (
                <SelectItem key={preprocessor} value={preprocessor}>
                  {preprocessor}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor={'preprocessor-params-' + index}>Params</Label>
          <Input
            id={'preprocessor-params-' + index}
            className="col-span-3"
            placeholder='{"max_length": 512}'
            required
            value={preprocessorInputs[index].params}
            onChange={(e) =>
              setPreprocessorInputs(
                preprocessorInputs.map((preprocessor, i) =>
                  i === index
                    ? { ...preprocessor, params: e.target.value }
                    : preprocessor
                )
              )
            }
          />
        </div>
      </div>
    </div>
  );
}

export function PreprocessDatasetDialog({
  datasetId,
  shardsets,
  preprocessors,
  children,
}: {
  datasetId: string;
  shardsets: Shardset[];
  preprocessors: string[];
  children: React.ReactNode;
}) {
  const [location, setLocation] = useState('');
  const [preprocessorInputs, setPreprocessorInputs] = useState<Preprocessor[]>(
    []
  );
  const [sourceShardsets, setSourceShardsets] = useState<string[]>([]);
  const [exportColumns, setExportColumns] = useState<string[]>([]);
  const [batchSize, setBatchSize] = useState(1);
  const [overwrite, setOverwrite] = useState(false);
  const [dropLast, setDropLast] = useState(false);
  const [open, setOpen] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  const reset = () => {
    setLocation('');
    setPreprocessorInputs([]);
    setSourceShardsets([]);
    setExportColumns([]);
    setBatchSize(1);
    formRef.current?.reset();
  };

  // Client action wrapper
  const clientAction = async (formData: FormData) => {
    // Add columns JSON to the form data before submitting
    let preprocessorsJson = '';
    try {
      const pp = preprocessorInputs.map((p) => ({
        name: p.name,
        params: JSON.parse(p.params),
      }));
      preprocessorsJson = JSON.stringify(pp);
    } catch (error) {
      toast.error('Invalid preprocessor params');
      return;
    }

    const result = await preprocessDataset(
      datasetId,
      location,
      sourceShardsets,
      preprocessorsJson,
      exportColumns,
      batchSize,
      overwrite,
      dropLast
    );

    if (result.success) {
      toast.success('Started preprocessing');
      setOpen(false);
      reset();
    } else {
      toast.error(`Failed to start preprocessing: ${result.error}`);
    }
  };

  if (preprocessors.length === 0) {
    return (
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>{children}</DialogTrigger>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>No preprocessors found!</DialogTitle>
            <DialogDescription>
              Please create a preprocessor first.
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Preprocess</DialogTitle>
          <DialogDescription>
            Generate a new shardset by preprocessing the dataset.
          </DialogDescription>
        </DialogHeader>

        <form ref={formRef} action={clientAction}>
          <div className="grid gap-4 py-4">
            <div className="text-lg mt-2">Source</div>
            {sourceShardsets.map((sourceShardset, index) => (
              <div
                key={`sourceShardset-${index}`}
                className="grid grid-cols-4 items-center gap-4"
              >
                <Label htmlFor="source" className="text-right">
                  Shardset
                </Label>
                <Select
                  name="source"
                  required
                  value={sourceShardset}
                  onValueChange={(value) =>
                    setSourceShardsets((prev) => {
                      const newSourceShardsets = [...prev];
                      newSourceShardsets[index] = value;
                      return newSourceShardsets;
                    })
                  }
                >
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Select a source" />
                  </SelectTrigger>
                  <SelectContent className="col-span-3">
                    {shardsets.map((shardset) => (
                      <SelectItem
                        key={shardset.id}
                        value={shardset.id}
                        disabled={sourceShardsets.includes(shardset.id)}
                      >
                        {shardset.location}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ))}
            {sourceShardsets.length < shardsets.length && (
              <Button
                type="button"
                variant="outline"
                onClick={() => setSourceShardsets([...sourceShardsets, ''])}
              >
                <Plus />
                Add Source Shardset
              </Button>
            )}
            <div className="text-lg mt-2 flex gap-2 items-center">
              <div>Preprocessors</div>
              <IconTooltip
                icon={<Info className="w-4 h-4" />}
                content={<p></p>}
              />
            </div>
            <ScrollArea className="max-h-[200px]">
              {preprocessorInputs.map((_, index) => (
                <div key={index}>
                  <PreprocessorInputs
                    index={index}
                    preprocessors={preprocessors}
                    preprocessorInputs={preprocessorInputs}
                    setPreprocessorInputs={setPreprocessorInputs}
                  />
                  <Separator className="my-2" />
                </div>
              ))}
            </ScrollArea>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                setPreprocessorInputs([
                  ...preprocessorInputs,
                  { name: '', params: '{}' },
                ])
              }
            >
              <Plus />
              Add Preprocessor
            </Button>
          </div>
          <div className="grid gap-4 py-4">
            <div className="text-lg mt-2">Configuration</div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="location" className="text-right">
                Batch Size
              </Label>
              <Input
                id="batch_size"
                name="batch_size"
                type="number"
                className="col-span-3"
                placeholder="100"
                required
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="grid gap-4 py-4">
            <div className="text-lg mt-2">Output</div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="location" className="text-right">
                Location
              </Label>
              <Input
                id="location"
                name="location"
                className="col-span-3"
                placeholder="s3://bucket/path/to/shardset/"
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="location" className="text-right">
                Overwrite
              </Label>
              <Checkbox
                id="overwrite"
                name="overwrite"
                checked={overwrite}
                onCheckedChange={(checked) =>
                  setOverwrite(checked === 'indeterminate' ? false : checked)
                }
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="location" className="text-right">
                Drop Last
              </Label>
              <Checkbox
                id="drop_last"
                name="drop_last"
                checked={dropLast}
                onCheckedChange={(checked) =>
                  setDropLast(checked === 'indeterminate' ? false : checked)
                }
              />
            </div>
            {exportColumns.map((column, index) => (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="location" className="text-right">
                  Export Column {index + 1}
                </Label>
                <Input
                  key={`export-column-${index}`}
                  id="location"
                  name="location"
                  className="col-span-3"
                  placeholder="new_column_name"
                  required
                  value={column}
                  onChange={(e) =>
                    setExportColumns((prev) => {
                      const newExportColumns = [...prev];
                      newExportColumns[index] = e.target.value;
                      return newExportColumns;
                    })
                  }
                />
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              className=""
              onClick={() => setExportColumns([...exportColumns, ''])}
            >
              <Plus />
              Add Export Column
            </Button>
          </div>
          <DialogFooter>
            <SubmitButton />
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
