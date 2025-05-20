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

export function Pagination({
  buttonCount,
  totalPages,
  currentPage,
  pageHref,
}: {
  buttonCount: number;
  totalPages: number;
  currentPage: number;
  pageHref: (page: number) => string;
}) {
  const buttonStartPage = Math.max(
    0,
    currentPage - (currentPage % buttonCount)
  );
  const buttonEndPage = Math.min(totalPages, buttonStartPage + buttonCount);
  const pageRange = Array.from(
    { length: buttonEndPage - buttonStartPage },
    (_, index) => buttonStartPage + index
  );

  return (
    <PaginationComponent>
      <PaginationContent>
        {buttonStartPage > 0 && (
          <>
            <PaginationItem>
              <PaginationPrevious
                href={pageHref(buttonStartPage - buttonCount)}
              />
            </PaginationItem>
          </>
        )}
        {pageRange.map((page) => (
          <PaginationItem key={page}>
            <PaginationLink
              href={pageHref(page)}
              isActive={currentPage === page}
            >
              {page + 1}
            </PaginationLink>
          </PaginationItem>
        ))}
        {totalPages > buttonEndPage && (
          <>
            <PaginationItem>
              <PaginationNext href={pageHref(buttonEndPage)} />
            </PaginationItem>
          </>
        )}
        <form className="flex items-center gap-2 text-sm text-muted-foreground">
          <div>
            <Input
              className="w-24"
              type="number"
              min={1}
              max={totalPages + 1}
              defaultValue={currentPage + 1}
            />
          </div>
          <div>/</div>
          <div>{totalPages}</div>
          <Button variant="outline" size="icon">
            <ArrowUpRight className="w-4" />
          </Button>
        </form>
      </PaginationContent>
    </PaginationComponent>
  );
}
