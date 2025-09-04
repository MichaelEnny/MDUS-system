import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/layout/Layout';
import FileUpload from './components/upload/FileUpload';
import DocumentList from './components/results/DocumentList';
import DocumentViewer from './components/results/DocumentViewer';
import ErrorBoundary from './components/ui/ErrorBoundary';
import { useWebSocket } from './hooks/useWebSocket';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

const AppContent: React.FC = () => {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  // WebSocket connection for real-time updates
  useWebSocket((data) => {
    console.log('WebSocket message received:', data);
    
    // Handle processing status updates
    if (data.type === 'processing_update') {
      // Invalidate relevant queries to refetch data
      queryClient.invalidateQueries({ 
        queryKey: ['processing-status', data.processingId] 
      });
      
      if (data.status === 'completed') {
        queryClient.invalidateQueries({ 
          queryKey: ['document-analysis', data.documentId] 
        });
      }
    }
  });

  const handleViewDocument = (documentId: string) => {
    setSelectedDocumentId(documentId);
  };

  const handleCloseDocument = () => {
    setSelectedDocumentId(null);
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header Section */}
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Document Processing & Analysis
          </h2>
          <p className="mt-4 text-lg text-gray-600 max-w-3xl mx-auto">
            Upload medical documents for AI-powered analysis with 99.2% accuracy. 
            Extract text, identify entities, and understand document structure automatically.
          </p>
        </div>

        {/* Document Viewer Modal */}
        {selectedDocumentId && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="w-full max-w-6xl max-h-[90vh] overflow-y-auto">
              <DocumentViewer
                documentId={selectedDocumentId}
                onClose={handleCloseDocument}
              />
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Upload Documents
              </h3>
              <FileUpload />
            </div>
          </div>

          {/* Documents List Section */}
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Your Documents
              </h3>
              <DocumentList onViewDocument={handleViewDocument} />
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-16">
          <div className="text-center mb-12">
            <h3 className="text-2xl font-bold text-gray-900">
              AI-Powered Document Understanding
            </h3>
            <p className="mt-4 text-lg text-gray-600">
              Advanced multi-modal processing for comprehensive document analysis
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-primary-600 text-2xl">📄</span>
              </div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                Text Extraction
              </h4>
              <p className="text-gray-600">
                Extract text from PDFs, images, and documents with OCR technology
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-success-600 text-2xl">🔍</span>
              </div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                Entity Recognition
              </h4>
              <p className="text-gray-600">
                Identify medical entities, dates, names, and key information automatically
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-warning-600 text-2xl">📊</span>
              </div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                Structure Analysis
              </h4>
              <p className="text-gray-600">
                Understand document layout, tables, and hierarchical structure
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppContent />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 5000,
            style: {
              background: '#fff',
              color: '#374151',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;