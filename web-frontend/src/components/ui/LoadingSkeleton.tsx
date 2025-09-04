import React from 'react';
import { clsx } from 'clsx';

interface LoadingSkeletonProps {
  lines?: number;
  height?: string;
  className?: string;
  animate?: boolean;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  lines = 1,
  height = 'h-4',
  className,
  animate = true
}) => {
  return (
    <div className={clsx('space-y-3', className)} role="status" aria-label="Loading">
      {Array.from({ length: lines }, (_, index) => (
        <div
          key={index}
          className={clsx(
            'bg-gray-200 rounded',
            height,
            animate && 'animate-pulse'
          )}
        />
      ))}
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export const CardSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={clsx('p-6 border rounded-lg bg-white', className)}>
    <div className="animate-pulse space-y-4">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="space-y-2">
        <div className="h-3 bg-gray-200 rounded"></div>
        <div className="h-3 bg-gray-200 rounded w-5/6"></div>
      </div>
      <div className="flex space-x-4">
        <div className="h-8 bg-gray-200 rounded w-20"></div>
        <div className="h-8 bg-gray-200 rounded w-20"></div>
      </div>
    </div>
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4
}) => (
  <div className="space-y-3">
    {Array.from({ length: rows }, (_, rowIndex) => (
      <div key={rowIndex} className="flex space-x-4">
        {Array.from({ length: columns }, (_, colIndex) => (
          <div
            key={colIndex}
            className="flex-1 h-4 bg-gray-200 rounded animate-pulse"
          />
        ))}
      </div>
    ))}
  </div>
);

export default LoadingSkeleton;