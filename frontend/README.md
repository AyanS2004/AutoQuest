# AutoQuest Frontend - Dashboard Architecture

A modern React-based dashboard for the AutoQuest RAG-powered document analysis system.

## UX/UI Goals

- **Clarity for researchers** → Show what queries are being run, progress status, and extracted outputs
- **Exploration** → Let users search and chat with the RAG bot (retrieves from processed SQLite/Excel)
- **Reliability** → Progress tracking, error logs, and retry visibility
- **Scalability** → Dashboard view for batches, company-wise drill-downs, and field-level details

## Architecture Overview

### Layout Structure
- **Left Sidebar** → Navigation tabs (Dashboard, Explorer, RAG Chat, Logs)
- **Main Panel** → Content area (Table, Progress Graphs, Chat)
- **Right Sidebar** → Live Logs / Batch Details (contextual)

### Key Pages

#### 1. Dashboard
- **System Status Cards**: Active session, total companies, success rate, documents
- **Progress Tracking**: Overall progress bar, current field progress
- **Quick Controls**: Start/Pause/Resume extraction, Export Excel
- **Recent Activity**: Session history with status indicators
- **Error Summary**: Failed extractions, retries, emergency saves

#### 2. Data Explorer
- **Search & Filters**: Company name, industry, status filtering
- **Interactive Data Grid**: Sortable columns with inline editing
- **Export Options**: Download as Excel/CSV
- **Confidence Indicators**: Perfect/Useful/Forced extraction confidence
- **URL Handling**: Clickable hyperlinks for websites

#### 3. RAG Chat Interface
- **Chat Panel**: Rich text input with message history
- **Source References**: Collapsible source panels with similarity scores
- **Integration**: "Show in Table" button to highlight relevant rows
- **Export**: Download chat conversations

#### 4. Logs & Monitoring
- **Real-time Streaming**: Live log updates with color coding
- **Filtering**: By level (Info/Warning/Error), search, visibility toggles
- **Error Recovery**: Failed extractions, retry attempts, emergency saves
- **Export**: Download logs as CSV

## 🛠️ Tech Stack

- **UI Framework**: React 18 + Tailwind CSS
- **Components**: Custom UI components with Radix UI primitives
- **Charts**: Recharts for progress visualization
- **Data Grid**: Custom implementation with sorting/filtering
- **State Management**: React hooks with context
- **API**: Axios for backend communication
- **Real-time**: WebSocket support for live updates

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation
```bash
cd frontend
npm install
```

### Development
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production
```bash
npm run build
```

## Project Structure

```
src/
├── components/
│   ├── Layout.jsx              # Main layout with sidebar
│   └── ui/                     # Reusable UI components
│       ├── Button.jsx
│       ├── Card.jsx
│       ├── Progress.jsx
│       └── Badge.jsx
├── pages/
│   ├── Dashboard.jsx           # Main dashboard
│   ├── DataExplorer.jsx        # Data grid view
│   ├── RagChat.jsx            # Chat interface
│   └── Logs.jsx               # Log monitoring
├── services/
│   └── api.js                 # API service layer
├── lib/
│   └── utils.js               # Utility functions
└── main.jsx                   # App entry point
```

## Configuration

### Environment Variables
Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

### API Endpoints
The frontend expects the following backend endpoints:

- `GET /health` - System health check
- `GET /gcc/sessions` - List extraction sessions
- `POST /gcc/start` - Start new extraction
- `GET /data/companies` - Get company data
- `POST /chat` - RAG chat endpoint
- `GET /logs` - Get system logs

## Design System

### Color Palette
- **Primary**: Blue (#3B82F6)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#EF4444)
- **Muted**: Gray (#6B7280)

### Status Indicators
- **Perfect**: Green badge (high confidence extraction)
- **Useful**: Blue badge (medium confidence)
- **Forced**: Red badge (low confidence/manual override)

### Progress States
- **Running**: Blue with spinner
- **Completed**: Green checkmark
- **Failed**: Red X
- **Pending**: Yellow warning

## Real-time Features

### WebSocket Integration
- Live progress updates
- Real-time log streaming
- Session status changes
- Error notifications

### Auto-refresh
- Dashboard stats every 10 seconds
- Log updates every 2 seconds
- Health checks every 30 seconds

## Data Flow

1. **Dashboard** → Shows high-level stats and controls
2. **Data Explorer** → Displays extracted company data with editing
3. **RAG Chat** → Interactive Q&A with document sources
4. **Logs** → Real-time system monitoring and debugging

## Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **API Errors**: User-friendly error messages
- **Validation**: Form validation with helpful feedback
- **Fallbacks**: Graceful degradation when services are unavailable

## Security

- **Authentication**: JWT token-based auth
- **CORS**: Configured for secure cross-origin requests
- **Input Sanitization**: All user inputs are sanitized
- **HTTPS**: Production deployment requires HTTPS

## Performance

- **Lazy Loading**: Components loaded on demand
- **Memoization**: React.memo for expensive components
- **Debouncing**: Search inputs debounced for performance
- **Virtualization**: Large data sets use virtual scrolling

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## License

This project is part of the AutoQuest system.
