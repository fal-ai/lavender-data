'use client';

import type { components } from '@/lib/api/v1';
import {
  Select,
  SelectItem,
  SelectContent,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { updateColumn } from './update-column-action';
import { useCallback, useState } from 'react';
import {
  AlertDialog,
  AlertDialogTitle,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogFooter,
} from '@/components/ui/alert-dialog';

const typeOptions: { value: string; label: string }[] = [
  { value: 'string', label: 'string' },
  { value: 'int64', label: 'int64' },
  { value: 'int32', label: 'int32' },
  { value: 'float', label: 'float' },
  { value: 'double', label: 'double' },
  { value: 'boolean', label: 'boolean' },
  { value: 'binary', label: 'binary' },
  { value: 'list', label: 'list' },
  { value: 'map', label: 'map' },
];

export function SelectColumnType({
  column,
  datasetId,
}: {
  column: components['schemas']['DatasetColumnPublic'];
  datasetId: string;
}) {
  const [type, setType] = useState<string>(column.type);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [open, setOpen] = useState<boolean>(false);

  const onSelectChange = useCallback((value: string) => {
    setType(value);
    setOpen(true);
  }, []);

  const onConfirm = useCallback(() => {
    setIsLoading(true);
    updateColumn(datasetId, column.id as string, {
      type,
    })
      .then(() => {
        setIsLoading(false);
      })
      .catch(() => {
        setIsLoading(false);
      });
  }, [datasetId, column.id, type]);

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <Select
        value={column.type}
        onValueChange={onSelectChange}
        disabled={isLoading}
      >
        <SelectTrigger className="font-mono text-xs">
          <SelectValue placeholder="Select a type" />
        </SelectTrigger>
        <SelectContent>
          {typeOptions.map((option) => (
            <SelectItem
              key={option.value}
              value={option.value}
              className="font-mono text-xs"
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>Continue</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
