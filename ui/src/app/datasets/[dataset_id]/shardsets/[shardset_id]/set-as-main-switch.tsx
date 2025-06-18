'use client';

import { useEffect, useState } from 'react';
import { Label } from '@/components/ui/label';
import { updateShardset } from './update-shardset-action';
import { Switch } from '@/components/ui/switch';

export function SetAsMainSwitch({
  dataset_id,
  shardset_id,
  is_main,
}: {
  dataset_id: string;
  shardset_id: string;
  is_main: boolean;
}) {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(false);
  }, [is_main]);

  return (
    <div className="flex items-center gap-2">
      <Label>Main</Label>
      <Switch
        checked={is_main}
        onCheckedChange={async (checked) => {
          setLoading(true);
          await updateShardset(dataset_id, shardset_id, checked);
        }}
        disabled={loading}
      />
    </div>
  );
}
