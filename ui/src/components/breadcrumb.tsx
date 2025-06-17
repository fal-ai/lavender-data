'use client';

import {
  Breadcrumb as BreadcrumbComponent,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb';
import { usePathname } from 'next/navigation';

export function Breadcrumb({}: {}) {
  const pathname = usePathname();
  return (
    <BreadcrumbComponent className="w-full pt-4">
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink href="/">Home</BreadcrumbLink>
        </BreadcrumbItem>
        {pathname
          .split('/')
          .filter((path) => path !== '')
          .map((path, index, arr) => [
            <BreadcrumbSeparator key={`separator-${index}`} />,
            <BreadcrumbItem key={index}>
              {index !== arr.length - 1 ? (
                <BreadcrumbLink href={`/${arr.slice(0, index + 1).join('/')}`}>
                  {path}
                </BreadcrumbLink>
              ) : (
                <BreadcrumbPage>{path}</BreadcrumbPage>
              )}
            </BreadcrumbItem>,
          ])}
      </BreadcrumbList>
    </BreadcrumbComponent>
  );
}
