'use client';

import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from '@/components/ui/alert-dialog';
import { deleteShardset } from './delete-shardset-action';
import { useRouter } from 'next/navigation';

export function DeleteShardsetDialog({
  datasetId,
  shardsetId,
}: {
  datasetId: string;
  shardsetId: string;
}) {
  const router = useRouter();

  const clientAction = async () => {
    const result = await deleteShardset(datasetId, shardsetId);

    if (result.success) {
      toast.success('Shardset deleted successfully');
      router.push(`/datasets/${datasetId}`);
    } else {
      toast.error(`Failed to delete shardset: ${result.error}`);
    }
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">Delete this shardset</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete your
            shardset and related shards. Of course, actual data will not be
            affected.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={clientAction}>Continue</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
