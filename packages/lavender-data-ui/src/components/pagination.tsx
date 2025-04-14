import { PaginationLink } from './ui/pagination';
import { Ellipsis } from 'lucide-react';
import { PaginationItem } from './ui/pagination';
import { PaginationContent } from './ui/pagination';
import { Pagination as PaginationComponent } from './ui/pagination';

export function Pagination({
  centerButtonCount,
  totalPages,
  currentPage,
  pageHref,
}: {
  centerButtonCount: number;
  totalPages: number;
  currentPage: number;
  pageHref: (page: number) => string;
}) {
  const buttonStartPage = Math.max(
    0,
    Math.min(
      currentPage - Math.floor(centerButtonCount / 2),
      totalPages - centerButtonCount
    )
  );
  const buttonEndPage = Math.min(
    totalPages,
    buttonStartPage + centerButtonCount
  );
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
              <PaginationLink href={pageHref(0)}>1</PaginationLink>
            </PaginationItem>
            <PaginationItem>
              <Ellipsis className="w-4" />
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
              <Ellipsis className="w-4" />
            </PaginationItem>
            <PaginationItem>
              <PaginationLink href={pageHref(totalPages - 1)}>
                {totalPages}
              </PaginationLink>
            </PaginationItem>
          </>
        )}
      </PaginationContent>
    </PaginationComponent>
  );
}
