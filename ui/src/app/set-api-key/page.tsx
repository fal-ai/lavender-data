'use client';

import { useCallback, useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { redirect } from 'next/navigation';
import { toast } from 'sonner';
import { setApiKey } from './set-api-key';

export default function SetApiKeyPage() {
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(async (formData: FormData) => {
    setLoading(true);
    const result = await setApiKey(formData);
    if (result.error) {
      toast.error(result.error);
    }
    if (result.redirect) {
      redirect(result.redirect);
    }
    setLoading(false);
  }, []);

  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center space-y-8 py-10">
      <Card className="w-[480px]">
        <CardHeader>
          <CardTitle>Set API Key</CardTitle>
          <CardDescription>
            Set the API key to use the Lavender Data Web UI. <br /> If you don't
            have an API key, please contact the administrator.
          </CardDescription>
        </CardHeader>
        <form action={handleSubmit}>
          <CardContent className="flex justify-end gap-2">
            <Input name="apiKey" type="password" placeholder="API Key" />
            <Button type="submit">Confirm</Button>
          </CardContent>
        </form>
      </Card>
    </main>
  );
}
