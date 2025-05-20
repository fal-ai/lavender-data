import { redirect } from 'next/navigation';

export default async function DatasetDetailPage({
  params,
}: {
  params: Promise<{
    dataset_id: string;
  }>;
}) {
  const { dataset_id } = await params;
  redirect(`/datasets/${dataset_id}/preview`);
}
