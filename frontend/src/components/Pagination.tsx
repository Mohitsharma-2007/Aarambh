import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/utils/cn';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({ currentPage, totalPages, onPageChange, className }: PaginationProps) {
  const pages = [];
  const showPages = 5;
  
  let startPage = Math.max(1, currentPage - Math.floor(showPages / 2));
  let endPage = Math.min(totalPages, startPage + showPages - 1);
  
  if (endPage - startPage + 1 < showPages) {
    startPage = Math.max(1, endPage - showPages + 1);
  }
  
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  return (
    <div className={cn("flex items-center justify-center gap-2 mt-6", className)}>
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={cn(
          "p-2 rounded-lg border-2 transition-all",
          "flex items-center justify-center",
          currentPage === 1 
            ? "opacity-50 cursor-not-allowed border-gray-200" 
            : "hover:bg-gray-50 border-gray-300 cursor-pointer"
        )}
      >
        <ChevronLeft className="w-4 h-4" />
      </button>

      {startPage > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-3 py-2 rounded-lg border-2 border-gray-300 hover:bg-gray-50 transition-all"
          >
            1
          </button>
          {startPage > 2 && <span className="px-2">...</span>}
        </>
      )}

      {pages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={cn(
            "px-3 py-2 rounded-lg border-2 transition-all font-medium",
            page === currentPage
              ? "bg-blue-500 text-white border-blue-500"
              : "border-gray-300 hover:bg-gray-50"
          )}
        >
          {page}
        </button>
      ))}

      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && <span className="px-2">...</span>}
          <button
            onClick={() => onPageChange(totalPages)}
            className="px-3 py-2 rounded-lg border-2 border-gray-300 hover:bg-gray-50 transition-all"
          >
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={cn(
          "p-2 rounded-lg border-2 transition-all",
          "flex items-center justify-center",
          currentPage === totalPages 
            ? "opacity-50 cursor-not-allowed border-gray-200" 
            : "hover:bg-gray-50 border-gray-300 cursor-pointer"
        )}
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}
