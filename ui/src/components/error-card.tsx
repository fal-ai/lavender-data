'use client';

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CircleAlert } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from './ui/button';

export function ErrorCard({
  error,
  returnBtn,
}: {
  error: any;
  returnBtn?: boolean;
}) {
  const router = useRouter();
  return (
    <div className="my-8 w-full flex flex-row justify-center">
      <Card className="w-[480px]">
        <CardHeader>
          <CardTitle>
            <div className="flex flex-row gap-2 items-center">
              <CircleAlert className="w-4 h-4 text-red-700" />
              <div>Error</div>
            </div>
          </CardTitle>
          <CardDescription>
            Please contact support if the problem persists.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p>{typeof error === 'string' ? error : JSON.stringify(error)}</p>
        </CardContent>
        {returnBtn && (
          <CardFooter>
            <div className="w-full flex flex-row gap-2 justify-end">
              <Button variant="outline" onClick={() => router.back()}>
                Return
              </Button>
            </div>
          </CardFooter>
        )}
      </Card>
    </div>
  );
}
