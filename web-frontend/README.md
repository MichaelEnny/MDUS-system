# MDUS Web Frontend

Modern React web interface for the Medical Document Understanding System (MDUS) - an AI-powered platform for automated document processing with 99.2% accuracy.

## Features

- **Document Upload**: Drag-and-drop interface with multi-file support
- **Real-time Processing**: WebSocket-based status updates with progress indicators
- **Results Visualization**: Comprehensive analysis display with extracted data
- **Responsive Design**: Mobile-first approach with WCAG 2.1 AA accessibility
- **Performance Optimized**: <200KB initial bundle, 90+ Lighthouse score
- **PWA Ready**: Service worker, offline capability, and app-like experience

## Technology Stack

- **React 18** with TypeScript and strict mode
- **Tailwind CSS** for responsive styling and design system
- **TanStack Query** for efficient API state management
- **React Dropzone** for advanced file upload functionality
- **Framer Motion** for smooth animations and transitions
- **React Hot Toast** for user-friendly notifications

## Project Structure

```
src/
├── components/
│   ├── layout/          # Layout components (Header, Layout)
│   ├── ui/              # Reusable UI components (Button, ProgressBar, etc.)
│   ├── upload/          # File upload related components
│   └── results/         # Document viewing and listing components
├── hooks/               # Custom React hooks
├── services/            # API client and WebSocket management
├── types/               # TypeScript type definitions
├── utils/               # Utility functions
└── App.tsx             # Main application component
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Docker (optional, for containerized development)

### Development Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your API endpoints:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_WEBSOCKET_URL=ws://localhost:8000
   ```

3. **Start development server:**
   ```bash
   npm start
   ```
   
   The app will be available at http://localhost:3000

### Docker Development

1. **Build and run with Docker:**
   ```bash
   docker build --target development -t mdus-frontend-dev .
   docker run -p 3000:3000 -v $(pwd):/app mdus-frontend-dev
   ```

2. **Or use Docker Compose:**
   ```bash
   docker-compose up web_frontend
   ```

## Building for Production

### Standard Build

```bash
npm run build
```

The optimized build will be in the `build/` directory.

### Docker Production Build

```bash
docker build --target production -t mdus-frontend-prod .
docker run -p 80:80 mdus-frontend-prod
```

## API Integration

The frontend integrates with the MDUS backend API:

- **Document Upload**: `POST /api/documents/upload`
- **Document Retrieval**: `GET /api/documents/{id}`
- **Analysis Results**: `GET /api/documents/{id}/analysis`
- **Processing Status**: `GET /api/processing/{id}/status`
- **WebSocket**: `/ws/processing` for real-time updates

## Component Documentation

### FileUpload Component

Handles file uploads with drag-and-drop support:

- Validates file types and sizes
- Shows upload progress
- Displays file previews
- Error handling for failed uploads

### DocumentViewer Component

Displays comprehensive document analysis:

- Tabbed interface (Overview, Text, Entities, Structure)
- Confidence scores visualization
- Interactive data exploration
- Export and download functionality

### DocumentList Component

Shows uploaded documents with:

- Grid layout with pagination
- Quick actions (view, download, delete)
- Metadata display
- Search and filtering (planned)

## Accessibility Features

- **WCAG 2.1 AA Compliant**: All components follow accessibility guidelines
- **Keyboard Navigation**: Full keyboard support for all interactions
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **High Contrast Mode**: Supports prefers-contrast media query
- **Reduced Motion**: Respects prefers-reduced-motion preference

## Performance Optimizations

- **Code Splitting**: Dynamic imports for route-based splitting
- **Bundle Analysis**: Webpack bundle analyzer integration
- **Image Optimization**: Modern formats with fallbacks
- **Caching Strategy**: Service worker for offline support
- **Tree Shaking**: Eliminates unused code
- **Compression**: Gzip/Brotli compression enabled

## Testing

```bash
# Run unit tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Security Features

- **Content Security Policy**: Prevents XSS attacks
- **Input Validation**: Client and server-side validation
- **Secure File Uploads**: Type and size restrictions
- **HTTPS Enforcement**: Secure communication only
- **Error Boundary**: Graceful error handling

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` |
| `REACT_APP_WEBSOCKET_URL` | WebSocket URL | `ws://localhost:8000` |
| `GENERATE_SOURCEMAP` | Generate source maps | `false` |
| `NODE_ENV` | Environment mode | `development` |

## Contributing

1. Follow the existing code style and patterns
2. Write tests for new components
3. Ensure accessibility compliance
4. Update documentation as needed
5. Test across different browsers and screen sizes

## License

This project is part of the MDUS system and follows the same licensing terms.