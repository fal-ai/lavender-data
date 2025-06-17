import { Breadcrumb } from '@/components/breadcrumb';

export default async function DatasetsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="container flex w-full flex-1 flex-col items-center justify-center gap-8">
      <Breadcrumb />

      {children}
    </main>
  );
}
