export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  file: File;
}

export interface DocumentMetadata {
  id: string;
  filename: string;
  originalName: string;
  fileSize: number;
  mimeType: string;
  uploadTimestamp: string;
  userId?: string;
  checksum: string;
  pageCount?: number;
}

export interface ProcessingStatus {
  id: string;
  documentId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  estimatedTimeRemaining?: number;
  errorMessage?: string;
  startedAt: string;
  completedAt?: string;
}

export interface DocumentAnalysis {
  id: string;
  documentId: string;
  extractedText: string;
  metadata: {
    language: string;
    documentType: string;
    pageCount: number;
    wordCount: number;
    characterCount: number;
  };
  confidence: {
    overall: number;
    textExtraction: number;
    structureDetection: number;
    entityRecognition: number;
  };
  entities: Entity[];
  structure: DocumentStructure;
  keywords: Keyword[];
  summary: string;
  createdAt: string;
}

export interface Entity {
  text: string;
  label: string;
  confidence: number;
  startOffset: number;
  endOffset: number;
}

export interface DocumentStructure {
  sections: DocumentSection[];
  tables: TableData[];
  images: ImageData[];
}

export interface DocumentSection {
  title: string;
  content: string;
  level: number;
  pageNumber: number;
  confidence: number;
}

export interface TableData {
  headers: string[];
  rows: string[][];
  pageNumber: number;
  confidence: number;
}

export interface ImageData {
  id: string;
  description: string;
  pageNumber: number;
  boundingBox: BoundingBox;
  confidence: number;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Keyword {
  text: string;
  relevance: number;
  frequency: number;
}

export interface DocumentUploadResponse {
  documentId: string;
  message: string;
  processingId: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}