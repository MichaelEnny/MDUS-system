import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { UploadedFile, DocumentUploadResponse, ApiError } from '../types/document';
import { validateFile, generateFileId } from '../utils/file';
import toast from 'react-hot-toast';

interface UploadProgress {
  [fileId: string]: number;
}

interface UseDocumentUploadReturn {
  uploadFiles: (files: File[]) => Promise<void>;
  uploadProgress: UploadProgress;
  isUploading: boolean;
  uploadedFiles: UploadedFile[];
  clearUploadedFiles: () => void;
  removeFile: (fileId: string) => void;
}

export function useDocumentUpload(): UseDocumentUploadReturn {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation<
    DocumentUploadResponse,
    ApiError,
    { file: File; fileId: string }
  >({
    mutationFn: async ({ file, fileId }) => {
      const onProgress = (progress: number) => {
        setUploadProgress(prev => ({ ...prev, [fileId]: progress }));
      };

      return apiClient.uploadDocument(file, onProgress);
    },
    onSuccess: (data, { file, fileId }) => {
      // Update progress to 100%
      setUploadProgress(prev => ({ ...prev, [fileId]: 100 }));
      
      // Show success message
      toast.success(`${file.name} uploaded successfully`);
      
      // Invalidate documents query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      
      // Clean up progress after a delay
      setTimeout(() => {
        setUploadProgress(prev => {
          const updated = { ...prev };
          delete updated[fileId];
          return updated;
        });
      }, 2000);
    },
    onError: (error, { file, fileId }) => {
      // Clear progress for failed upload
      setUploadProgress(prev => {
        const updated = { ...prev };
        delete updated[fileId];
        return updated;
      });
      
      // Remove file from uploaded files list
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
      
      // Show error message
      toast.error(`Failed to upload ${file.name}: ${error.message}`);
    },
  });

  const uploadFiles = useCallback(async (files: File[]) => {
    // Validate files
    const validFiles: Array<{ file: File; fileId: string }> = [];
    
    for (const file of files) {
      const validation = validateFile(file);
      if (!validation.isValid) {
        toast.error(`${file.name}: ${validation.error}`);
        continue;
      }
      
      const fileId = generateFileId();
      validFiles.push({ file, fileId });
      
      // Add to uploaded files list
      setUploadedFiles(prev => [
        ...prev,
        {
          id: fileId,
          name: file.name,
          size: file.size,
          type: file.type,
          file,
        },
      ]);
    }

    // Upload files sequentially to avoid overwhelming the server
    for (const { file, fileId } of validFiles) {
      try {
        await uploadMutation.mutateAsync({ file, fileId });
      } catch (error) {
        // Error is handled in onError callback
        console.error('Upload failed:', error);
      }
    }
  }, [uploadMutation]);

  const clearUploadedFiles = useCallback(() => {
    setUploadedFiles([]);
    setUploadProgress({});
  }, []);

  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
    setUploadProgress(prev => {
      const updated = { ...prev };
      delete updated[fileId];
      return updated;
    });
  }, []);

  return {
    uploadFiles,
    uploadProgress,
    isUploading: uploadMutation.isPending,
    uploadedFiles,
    clearUploadedFiles,
    removeFile,
  };
}