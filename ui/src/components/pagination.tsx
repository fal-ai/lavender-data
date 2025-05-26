'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
} from './ui/pagination';
import { ArrowUpRight } from 'lucide-react';
import { PaginationItem } from './ui/pagination';
import { PaginationContent } from './ui/pagination';
import { Pagination as PaginationComponent } from './ui/pagination';
import { Input } from './ui/input';
import { Button } from './ui/button';

export const getPageRange = ({
  buttonCount,
  totalPages,
  currentPage,
}: {
  buttonCount: number;
  totalPages: number;
  currentPage: number;
}) => {
  const buttonStartPage = Math.max(
    0,
    currentPage - (currentPage % buttonCount)
  );
  const buttonEndPage = Math.min(totalPages, buttonStartPage + buttonCount);
  const pageRange = Array.from(
    { length: buttonEndPage - buttonStartPage },
    (_, index) => buttonStartPage + index
  );
  return pageRange;
};

export function Pagination({
  buttonCount,
  totalPages,
  currentPage,
  pageHref,
}: {
  buttonCount: number;
  totalPages: number;
  currentPage: number;
  pageHref: string;
}) {
  const [page, setPage] = useState<number>(currentPage);

  useEffect(() => {
    setPage(currentPage);
  }, [currentPage]);

  const pageRange = getPageRange({
    buttonCount,
    totalPages,
    currentPage,
  });

  const buttonStartPage = pageRange[0];
  const buttonEndPage = pageRange[pageRange.length - 1];

  const getPageHref = (page: number) => {
    return pageHref.replace('{page}', `${page}`);
  };

  return (
    <PaginationComponent>
      <PaginationContent>
        {buttonStartPage > 0 && (
          <>
            <PaginationItem>
              <PaginationPrevious
                href={getPageHref(buttonStartPage - buttonCount)}
              />
            </PaginationItem>
          </>
        )}
        {pageRange.map((page) => (
          <PaginationItem key={page}>
            <PaginationLink
              href={getPageHref(page)}
              isActive={currentPage === page}
            >
              {page + 1}
            </PaginationLink>
          </PaginationItem>
        ))}
        {totalPages > buttonEndPage && (
          <>
            <PaginationItem>
              <PaginationNext href={getPageHref(buttonEndPage)} />
            </PaginationItem>
          </>
        )}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div>
            <Input
              className="w-24 text-right"
              type="number"
              min={1}
              max={totalPages + 1}
              value={page + 1}
              onChange={(e) => setPage(Number(e.target.value) - 1)}
            />
          </div>
          <div>/</div>
          <div>{totalPages}</div>
          <Button variant="outline" size="icon">
            <Link href={getPageHref(page)}>
              <ArrowUpRight className="w-4" />
            </Link>
          </Button>
        </div>
      </PaginationContent>
    </PaginationComponent>
  );
}
