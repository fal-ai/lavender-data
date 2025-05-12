'use client';

import { useState, useRef } from 'react';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { useFormStatus } from 'react-dom';
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
import { createDataset } from './add-dataset-action';

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" disabled={pending}>
      {pending ? 'Saving...' : 'Save'}
    </Button>
  );
}

export function AddDatasetDialog({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const router = useRouter();

  // Use server action with client-side wrapper for UI feedback
  const clientAction = async (formData: FormData) => {
    const result = await createDataset(formData);

    if (result.success) {
      toast.success('Dataset added successfully');
      setOpen(false);
      formRef.current?.reset();
      router.refresh();
    } else {
      toast.error(`Failed to add dataset: ${result.error}`);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>New dataset</DialogTitle>
          <DialogDescription>Add a new dataset.</DialogDescription>
        </DialogHeader>

        <form ref={formRef} action={clientAction}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name
              </Label>
              <Input
                id="name"
                name="name"
                className="col-span-3"
                placeholder="my-dataset"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="uidColumnName" className="text-right">
                UID Column
              </Label>
              <Input
                id="uidColumnName"
                name="uidColumnName"
                className="col-span-3"
                placeholder="id"
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
