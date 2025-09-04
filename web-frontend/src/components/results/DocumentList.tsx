import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DocumentTextIcon,
  EyeIcon,
  TrashIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import Button from '@/components/ui/Button';
import LoadingSkeleton, { CardSkeleton } from '@/components/ui/LoadingSkeleton';
import { apiClient } from '@/services/api';
import { DocumentMetadata } from '@/types/document';
import { formatDate, formatRelativeTime } from '@/utils/format';
import { formatFileSize } from '@/utils/file';
import toast from 'react-hot-toast';

interface DocumentListProps {
  onViewDocument?: (documentId: string) => void;
  className?: string;
}

const DocumentList: React.FC<DocumentListProps> = ({
  onViewDocument,
  className
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const queryClient = useQueryClient();

  // Fetch documents
  const {
    data: documentData,
    isLoading,
    error,
    isError,
  } = useQuery({
    queryKey: ['documents', currentPage, pageSize],
    queryFn: () => apiClient.getDocuments(currentPage, pageSize),
    keepPreviousData: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => apiClient.deleteDocument(documentId),
    onSuccess: (_, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document deleted successfully');
    },
    onError: (error) => {
      toast.error(`Failed to delete document: ${error.message}`);
    },
  });

  const handleDelete = async (documentId: string, filename: string) => {
    if (window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      deleteMutation.mutate(documentId);
    }
  };

  const handleDownload = async (documentId: string, filename: string) => {
    try {
      const blob = await apiClient.downloadDocument(documentId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Download started');
    } catch (error) {
      toast.error('Download failed');
    }
  };

  if (isLoading) {
    return (
      <div className={clsx('space-y-4', className)}>
        {Array.from({ length: 5 }, (_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError || !documentData) {
    return (
      <div className={clsx('text-center py-8', className)}>
        <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Failed to load documents
        </h3>
        <p className="text-sm text-gray-600">
          {error?.message || 'An error occurred while loading documents.'}
        </p>
      </div>
    );
  }

  const { documents, total, totalPages } = documentData;

  if (documents.length === 0) {
    return (
      <div className={clsx('text-center py-8', className)}>
        <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No documents uploaded yet
        </h3>
        <p className="text-sm text-gray-600">
          Upload your first document to get started with analysis.
        </p>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {documents.map((document) => (
          <div
            key={document.id}
            className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="p-6">
              {/* Document Icon and Info */}
              <div className="flex items-start space-x-3 mb-4">
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="w-8 h-8 text-primary-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 truncate" title={document.originalName}>
                    {document.originalName}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatFileSize(document.fileSize)} • {document.mimeType}
                  </p>
                  {document.pageCount && (
                    <p className="text-xs text-gray-500">
                      {document.pageCount} page{document.pageCount !== 1 ? 's' : ''}
                    </p>
                  )}
                </div>
              </div>

              {/* Metadata */}
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Uploaded:</span>
                  <span className="text-gray-900" title={formatDate(document.uploadTimestamp)}>
                    {formatRelativeTime(document.uploadTimestamp)}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Checksum:</span>
                  <span className="text-gray-900 font-mono">
                    {document.checksum.substring(0, 8)}...
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex space-x-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onViewDocument?.(document.id)}
                  leftIcon={<EyeIcon className="w-4 h-4" />}
                  className="flex-1"
                >
                  View
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDownload(document.id, document.originalName)}
                  aria-label="Download document"
                >
                  <ArrowDownTrayIcon className="w-4 h-4" />
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(document.id, document.originalName)}
                  disabled={deleteMutation.isPending}
                  aria-label="Delete document"
                  className="text-error-600 hover:text-error-700 hover:bg-error-50"
                >
                  <TrashIcon className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 pt-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <Button
              variant="outline"
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
            >
              Next
            </Button>
          </div>
          
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing{' '}
                <span className="font-medium">
                  {(currentPage - 1) * pageSize + 1}
                </span>{' '}
                to{' '}
                <span className="font-medium">
                  {Math.min(currentPage * pageSize, total)}
                </span>{' '}
                of{' '}
                <span className="font-medium">{total}</span>{' '}
                results
              </p>
            </div>
            
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="rounded-r-none"
                >
                  Previous
                </Button>
                
                {/* Page Numbers */}
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let pageNumber;
                  if (totalPages <= 5) {
                    pageNumber = i + 1;
                  } else if (currentPage <= 3) {
                    pageNumber = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNumber = totalPages - 4 + i;
                  } else {
                    pageNumber = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNumber}
                      onClick={() => setCurrentPage(pageNumber)}
                      className={clsx(
                        'relative inline-flex items-center px-4 py-2 border text-sm font-medium transition-colors',
                        currentPage === pageNumber
                          ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                          : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                      )}
                    >
                      {pageNumber}
                    </button>
                  );
                })}
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="rounded-l-none"
                >
                  Next
                </Button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentList;