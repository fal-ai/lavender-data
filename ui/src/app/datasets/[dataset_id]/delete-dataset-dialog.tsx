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
import { deleteDataset } from './delete-dataset-action';
import { useRouter } from 'next/navigation';

export function DeleteDatasetDialog({
  datasetId,
  children,
}: {
  datasetId: string;
  children: React.ReactNode;
}) {
  const router = useRouter();

  const clientAction = async () => {
    const result = await deleteDataset(datasetId);

    if (result.success) {
      toast.success('Dataset deleted successfully');
      router.push('/datasets');
    } else {
      toast.error(`Failed to delete dataset: ${result.error}`);
    }
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete your
            dataset, related shardsets and iterations. Of course, actual data
            will not be affected.
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
