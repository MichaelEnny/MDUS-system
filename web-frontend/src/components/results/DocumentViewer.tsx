import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DocumentTextIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  ChartBarIcon,
  TagIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon } from '@heroicons/react/24/solid';
import { clsx } from 'clsx';
import Button from '@/components/ui/Button';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import { apiClient } from '@/services/api';
import { DocumentAnalysis, ProcessingStatus } from '@/types/document';
import { formatDate, formatRelativeTime, formatConfidence } from '@/utils/format';

interface DocumentViewerProps {
  documentId: string;
  onClose?: () => void;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({ documentId, onClose }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'text' | 'entities' | 'structure'>('overview');

  // Fetch document analysis
  const {
    data: analysis,
    isLoading: isLoadingAnalysis,
    error: analysisError,
  } = useQuery<DocumentAnalysis>({
    queryKey: ['document-analysis', documentId],
    queryFn: () => apiClient.getDocumentAnalysis(documentId),
    retry: 3,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch processing status
  const {
    data: status,
    isLoading: isLoadingStatus,
  } = useQuery<ProcessingStatus>({
    queryKey: ['processing-status', documentId],
    queryFn: () => apiClient.getProcessingStatus(documentId),
    refetchInterval: (data) => {
      // Stop refetching when processing is complete
      return data?.status === 'completed' || data?.status === 'failed' ? false : 2000;
    },
  });

  const handleDownload = async () => {
    try {
      const blob = await apiClient.downloadDocument(documentId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = analysis?.metadata.language || 'document';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const getStatusIcon = (status: ProcessingStatus['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-success-500" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-error-500" />;
      case 'processing':
        return <div className="w-5 h-5 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />;
      default:
        return <ClockIcon className="w-5 h-5 text-warning-500" />;
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: ChartBarIcon },
    { id: 'text', label: 'Extracted Text', icon: DocumentTextIcon },
    { id: 'entities', label: 'Entities', icon: TagIcon },
    { id: 'structure', label: 'Structure', icon: EyeIcon },
  ] as const;

  if (isLoadingAnalysis || isLoadingStatus) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <LoadingSkeleton lines={10} className="space-y-6" />
      </div>
    );
  }

  if (analysisError || !analysis) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 text-center">
        <ExclamationTriangleIcon className="w-12 h-12 text-error-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Failed to load document analysis
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          {analysisError?.message || 'An error occurred while loading the document.'}
        </p>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold text-gray-900 truncate">
              Document Analysis
            </h2>
            <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
              <span>Pages: {analysis.metadata.pageCount}</span>
              <span>Words: {analysis.metadata.wordCount.toLocaleString()}</span>
              <span>Language: {analysis.metadata.language}</span>
              <span>Type: {analysis.metadata.documentType}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            {status && (
              <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100">
                {getStatusIcon(status.status)}
                <span className="text-sm font-medium capitalize">
                  {status.status}
                </span>
              </div>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              leftIcon={<ArrowDownTrayIcon className="w-4 h-4" />}
            >
              Download
            </Button>
            
            {onClose && (
              <Button variant="ghost" size="sm" onClick={onClose}>
                Close
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm',
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
                aria-current={activeTab === tab.id ? 'page' : undefined}
              >
                <Icon className="w-5 h-5 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Confidence Scores */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Confidence Scores</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(analysis.confidence).map(([key, value]) => {
                  const formatted = formatConfidence(value);
                  return (
                    <div key={key} className="bg-gray-50 rounded-lg p-4 text-center">
                      <div className={clsx('text-2xl font-bold', formatted.color)}>
                        {formatted.value}
                      </div>
                      <div className="text-sm text-gray-600 capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </div>
                      <div className={clsx('text-xs font-medium mt-1', formatted.color)}>
                        {formatted.label}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Summary */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 leading-relaxed">
                  {analysis.summary || 'No summary available.'}
                </p>
              </div>
            </div>

            {/* Keywords */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Top Keywords</h3>
              <div className="flex flex-wrap gap-2">
                {analysis.keywords.slice(0, 20).map((keyword, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800"
                  >
                    {keyword.text}
                    <span className="ml-1 text-xs text-primary-600">
                      ({keyword.frequency})
                    </span>
                  </span>
                ))}
              </div>
            </div>

            {/* Processing Info */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Processing Information</h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Created:</span>
                  <span className="text-gray-900">{formatDate(analysis.createdAt)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Processed:</span>
                  <span className="text-gray-900">{formatRelativeTime(analysis.createdAt)}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'text' && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Extracted Text</h3>
            <div className="bg-gray-50 rounded-lg p-6 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700 leading-relaxed">
                {analysis.extractedText || 'No text extracted.'}
              </pre>
            </div>
          </div>
        )}

        {activeTab === 'entities' && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Named Entities</h3>
            {analysis.entities.length > 0 ? (
              <div className="space-y-4">
                {Object.entries(
                  analysis.entities.reduce((acc, entity) => {
                    if (!acc[entity.label]) acc[entity.label] = [];
                    acc[entity.label].push(entity);
                    return acc;
                  }, {} as Record<string, typeof analysis.entities>)
                ).map(([label, entities]) => (
                  <div key={label}>
                    <h4 className="text-md font-medium text-gray-800 mb-2 capitalize">
                      {label} ({entities.length})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {entities.map((entity, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                        >
                          {entity.text}
                          <span className="ml-1 text-xs text-blue-600">
                            {Math.round(entity.confidence * 100)}%
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No entities detected.</p>
            )}
          </div>
        )}

        {activeTab === 'structure' && (
          <div className="space-y-6">
            {/* Sections */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Document Sections</h3>
              {analysis.structure.sections.length > 0 ? (
                <div className="space-y-3">
                  {analysis.structure.sections.map((section, index) => (
                    <div key={index} className="border-l-4 border-primary-200 pl-4">
                      <h4 className="font-medium text-gray-900">{section.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{section.content}</p>
                      <div className="text-xs text-gray-500 mt-2">
                        Page {section.pageNumber} • Level {section.level} • 
                        Confidence: {Math.round(section.confidence * 100)}%
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No sections detected.</p>
              )}
            </div>

            {/* Tables */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Tables</h3>
              {analysis.structure.tables.length > 0 ? (
                <div className="space-y-4">
                  {analysis.structure.tables.map((table, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 border-b">
                        <span className="text-sm font-medium">
                          Table {index + 1} (Page {table.pageNumber})
                        </span>
                        <span className="ml-2 text-xs text-gray-500">
                          Confidence: {Math.round(table.confidence * 100)}%
                        </span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              {table.headers.map((header, hIndex) => (
                                <th key={hIndex} className="px-4 py-2 text-left font-medium text-gray-900">
                                  {header}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {table.rows.slice(0, 5).map((row, rIndex) => (
                              <tr key={rIndex}>
                                {row.map((cell, cIndex) => (
                                  <td key={cIndex} className="px-4 py-2 text-gray-700">
                                    {cell}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {table.rows.length > 5 && (
                          <div className="px-4 py-2 text-xs text-gray-500 bg-gray-50">
                            ... and {table.rows.length - 5} more rows
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No tables detected.</p>
              )}
            </div>

            {/* Images */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Images</h3>
              {analysis.structure.images.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysis.structure.images.map((image, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">Image {index + 1}</h4>
                      <p className="text-sm text-gray-600 mb-2">{image.description}</p>
                      <div className="text-xs text-gray-500">
                        Page {image.pageNumber} • 
                        Confidence: {Math.round(image.confidence * 100)}%
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No images detected.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentViewer;