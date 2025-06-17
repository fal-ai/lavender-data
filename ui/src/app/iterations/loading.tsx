import { LoaderCircle } from 'lucide-react';

export default function Loading() {
  return (
    <div className="w-full flex gap-2 p-4 justify-center items-center text-muted-foreground">
      <LoaderCircle className="w-4 h-4 animate-spin" />
      <div className="text-sm">Loading...</div>
    </div>
  );
}
