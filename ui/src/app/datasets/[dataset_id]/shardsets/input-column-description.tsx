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
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Edit, Save } from 'lucide-react';

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

export function InputColumnDescription({
  column,
  datasetId,
}: {
  column: components['schemas']['DatasetColumnPublic'];
  datasetId: string;
}) {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [description, setDescription] = useState<string>(
    column.description ?? ''
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const onSave = useCallback(() => {
    setIsLoading(true);
    updateColumn(datasetId, column.id as string, {
      description,
    })
      .then(() => {
        setIsLoading(false);
        setIsEditing(false);
      })
      .catch(() => {
        setIsLoading(false);
        setIsEditing(false);
      });
  }, [datasetId, column.id, description]);

  return (
    <div className="flex justify-between items-center gap-2">
      {isEditing ? (
        <Input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      ) : (
        <div>{column.description}</div>
      )}
      {isEditing ? (
        <Button
          onClick={onSave}
          disabled={isLoading}
          variant="outline"
          size="icon"
        >
          <Save />
        </Button>
      ) : (
        <Button
          onClick={() => setIsEditing(true)}
          disabled={isLoading}
          variant="outline"
          size="icon"
        >
          <Edit />
        </Button>
      )}
    </div>
  );
}
