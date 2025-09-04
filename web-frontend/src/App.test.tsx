import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';

// Mock the WebSocket hook to avoid connection errors in tests
jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: false,
    sendMessage: jest.fn(),
    lastMessage: null,
    connectionError: null,
  }),
}));

// Create a test query client
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});

describe('App Component', () => {
  test('renders without crashing', () => {
    const queryClient = createTestQueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    
    expect(screen.getByText('Medical Document Understanding System')).toBeInTheDocument();
  });

  test('displays main heading', () => {
    const queryClient = createTestQueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    
    expect(screen.getByText('Document Processing & Analysis')).toBeInTheDocument();
  });

  test('shows upload and documents sections', () => {
    const queryClient = createTestQueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    
    expect(screen.getByText('Upload Documents')).toBeInTheDocument();
    expect(screen.getByText('Your Documents')).toBeInTheDocument();
  });
});