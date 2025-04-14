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
import { createShardset, ColumnInput } from './add-shardset-action';

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" disabled={pending}>
      {pending ? 'Saving...' : 'Save'}
    </Button>
  );
}

function ColumnInputs({
  index,
  columns,
  setColumns,
}: {
  index: number;
  columns: ColumnInput[];
  setColumns: (columns: ColumnInput[]) => void;
}) {
  return (
    <div className="my-4">
      <div className="flex flex-col gap-2">
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor={'column-name-' + index}>Name</Label>
          <Input
            id={'column-name-' + index}
            className="col-span-3"
            placeholder="caption"
            required
            value={columns[index].name}
            onChange={(e) =>
              setColumns(
                columns.map((column, i) =>
                  i === index ? { ...column, name: e.target.value } : column
                )
              )
            }
          />
        </div>
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor={'column-type-' + index}>Type</Label>
          <Input
            id={'column-type-' + index}
            className="col-span-3"
            placeholder="text"
            required
            value={columns[index].type}
            onChange={(e) =>
              setColumns(
                columns.map((column, i) =>
                  i === index ? { ...column, type: e.target.value } : column
                )
              )
            }
          />
        </div>
        <div className="grid grid-cols-4 items-center gap-4">
          <Label
            className="flex flex-col items-start gap-0"
            htmlFor={'column-description-' + index}
          >
            <div>Description</div>
            <div className="text-xs text-muted-foreground">(Optional)</div>
          </Label>
          <Input
            id={'column-description-' + index}
            className="col-span-3"
            placeholder="A caption for the image"
            value={columns[index].description ?? ''}
            onChange={(e) =>
              setColumns(
                columns.map((column, i) =>
                  i === index
                    ? { ...column, description: e.target.value }
                    : column
                )
              )
            }
          />
        </div>
      </div>
    </div>
  );
}

export function AddShardsetDialog({
  datasetId,
  children,
}: {
  datasetId: string;
  children: React.ReactNode;
}) {
  const [location, setLocation] = useState('');
  const [columns, setColumns] = useState<ColumnInput[]>([]);
  const [open, setOpen] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  // Client action wrapper
  const clientAction = async (formData: FormData) => {
    // Add columns JSON to the form data before submitting
    formData.set('columnsJson', JSON.stringify(columns));

    const result = await createShardset(datasetId, formData);

    if (result.success) {
      toast.success('Shardset added successfully');
      setOpen(false);
      setLocation('');
      setColumns([]);
      formRef.current?.reset();
    } else {
      toast.error(`Failed to add shardset: ${result.error}`);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>New shardset</DialogTitle>
          <DialogDescription>
            Add a new shardset with columns to the dataset.
          </DialogDescription>
        </DialogHeader>

        <form ref={formRef} action={clientAction}>
          <div className="grid gap-4 py-4">
            <div className="text-lg mt-2">Shardset</div>
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
            <div className="text-lg mt-2 flex gap-2 items-center">
              <div>Columns</div>
              <IconTooltip
                icon={<Info className="w-4 h-4" />}
                content={
                  <p>
                    If you have at least one shard in the location, the columns
                    will be inferred from the shard. <br />
                    Please specify columns if you want to override them or if
                    you don't have any shards yet.
                  </p>
                }
              />
            </div>
            <ScrollArea className="max-h-[200px]">
              {columns.map((column, index) => (
                <div key={index}>
                  <ColumnInputs
                    index={index}
                    columns={columns}
                    setColumns={setColumns}
                  />
                  <Separator className="my-2" />
                </div>
              ))}
            </ScrollArea>
            <Button
              type="button"
              variant="outline"
              onClick={() => setColumns([...columns, { name: '', type: '' }])}
            >
              <Plus />
              Add Column
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
