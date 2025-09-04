import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { DocumentArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon } from '@heroicons/react/24/solid';
import { clsx } from 'clsx';
import Button from '@/components/ui/Button';
import ProgressBar from '@/components/ui/ProgressBar';
import { useDocumentUpload } from '@/hooks/useDocumentUpload';
import { formatFileSize, ACCEPTED_FILE_TYPES, MAX_FILES } from '@/utils/file';

const FileUpload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const {
    uploadFiles,
    uploadProgress,
    isUploading,
    uploadedFiles,
    clearUploadedFiles,
    removeFile,
  } = useDocumentUpload();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      uploadFiles(acceptedFiles);
    }
    setDragActive(false);
  }, [uploadFiles]);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    fileRejections
  } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxFiles: MAX_FILES,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
  });

  const handleClearAll = () => {
    clearUploadedFiles();
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={clsx(
          'relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
          {
            'border-primary-300 bg-primary-50': isDragActive || dragActive,
            'border-gray-300 hover:border-gray-400': !isDragActive && !dragActive,
          }
        )}
        role="button"
        tabIndex={0}
        aria-label="File upload area"
      >
        <input {...getInputProps()} aria-describedby="file-upload-description" />
        
        <div className="space-y-4">
          <DocumentArrowUpIcon
            className={clsx(
              'mx-auto w-12 h-12',
              isDragActive || dragActive ? 'text-primary-500' : 'text-gray-400'
            )}
            aria-hidden="true"
          />
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop files here' : 'Upload documents'}
            </p>
            <p id="file-upload-description" className="text-sm text-gray-600 mt-2">
              Drag and drop files here, or click to select files
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Supports PDF, images, and documents up to {formatFileSize(10 * 1024 * 1024)}
            </p>
          </div>
          
          <Button
            variant="primary"
            size="lg"
            disabled={isUploading}
            className="mx-auto"
          >
            Select Files
          </Button>
        </div>
      </div>

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <div className="mt-4 p-4 bg-error-50 border border-error-200 rounded-lg">
          <h3 className="text-sm font-medium text-error-800 mb-2">
            Some files were rejected:
          </h3>
          <ul className="text-sm text-error-700 space-y-1">
            {fileRejections.map(({ file, errors }) => (
              <li key={file.name}>
                <strong>{file.name}</strong>: {errors.map(e => e.message).join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Uploaded Files ({uploadedFiles.length})
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearAll}
              disabled={isUploading}
            >
              Clear All
            </Button>
          </div>

          <div className="space-y-3">
            {uploadedFiles.map((file) => {
              const progress = uploadProgress[file.id];
              const isComplete = progress === 100;
              const isUploading = progress !== undefined && progress < 100;

              return (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg shadow-sm"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {isComplete ? (
                          <CheckCircleIcon className="w-6 h-6 text-success-500" aria-label="Upload complete" />
                        ) : isUploading ? (
                          <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" aria-label="Uploading" />
                        ) : (
                          <DocumentArrowUpIcon className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(file.size)} • {file.type}
                        </p>
                      </div>
                    </div>

                    {isUploading && (
                      <div className="mt-3">
                        <ProgressBar
                          value={progress}
                          size="sm"
                          color="primary"
                          showLabel
                          label="Uploading"
                        />
                      </div>
                    )}
                  </div>

                  <div className="flex-shrink-0 ml-4">
                    <button
                      onClick={() => removeFile(file.id)}
                      disabled={isUploading}
                      className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                      aria-label={`Remove ${file.name}`}
                    >
                      <XMarkIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Instructions */}
      {uploadedFiles.length === 0 && (
        <div className="mt-6 text-center">
          <div className="text-sm text-gray-600 space-y-2">
            <p>Supported formats:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {Object.values(ACCEPTED_FILE_TYPES).flat().map((ext) => (
                <span
                  key={ext}
                  className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800"
                >
                  {ext.toUpperCase()}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;