import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  DocumentMetadata,
  DocumentAnalysis,
  ProcessingStatus,
  DocumentUploadResponse,
  ApiError
} from '@/types/document';

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const apiError: ApiError = {
          message: error.response?.data?.message || error.message || 'An error occurred',
          code: error.response?.data?.code || error.code,
          details: error.response?.data?.details || {}
        };
        return Promise.reject(apiError);
      }
    );
  }

  // Document upload
  async uploadDocument(file: File, onUploadProgress?: (progress: number) => void): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response: AxiosResponse<DocumentUploadResponse> = await this.client.post(
      '/api/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onUploadProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onUploadProgress(progress);
          }
        },
      }
    );

    return response.data;
  }

  // Get document metadata
  async getDocument(documentId: string): Promise<DocumentMetadata> {
    const response: AxiosResponse<DocumentMetadata> = await this.client.get(
      `/api/documents/${documentId}`
    );
    return response.data;
  }

  // Get document analysis results
  async getDocumentAnalysis(documentId: string): Promise<DocumentAnalysis> {
    const response: AxiosResponse<DocumentAnalysis> = await this.client.get(
      `/api/documents/${documentId}/analysis`
    );
    return response.data;
  }

  // Get processing status
  async getProcessingStatus(processingId: string): Promise<ProcessingStatus> {
    const response: AxiosResponse<ProcessingStatus> = await this.client.get(
      `/api/processing/${processingId}/status`
    );
    return response.data;
  }

  // Get list of documents
  async getDocuments(page = 1, limit = 10): Promise<{
    documents: DocumentMetadata[];
    total: number;
    page: number;
    totalPages: number;
  }> {
    const response = await this.client.get('/api/documents', {
      params: { page, limit }
    });
    return response.data;
  }

  // Delete document
  async deleteDocument(documentId: string): Promise<void> {
    await this.client.delete(`/api/documents/${documentId}`);
  }

  // Download document
  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await this.client.get(`/api/documents/${documentId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/api/health');
    return response.data;
  }
}

// WebSocket client for real-time updates
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval = 5000;
  private maxReconnectAttempts = 10;
  private reconnectAttempts = 0;

  constructor() {
    this.url = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000';
  }

  connect(): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.url}/ws/processing`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve(this.ws!);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.handleReconnect();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectInterval);
    }
  }

  onMessage(callback: (data: any) => void) {
    if (this.ws) {
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          callback(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const apiClient = new ApiClient();
export const wsClient = new WebSocketClient();