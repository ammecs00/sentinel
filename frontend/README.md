# Sentinel Frontend - Employee Monitoring System

Modern React-based frontend for the Sentinel employee monitoring system.

## Features

- ✅ Modern React 18 with Hooks
- ✅ React Router for navigation
- ✅ Context API for state management
- ✅ Axios for API calls
- ✅ Responsive design
- ✅ Role-based access control
- ✅ Real-time updates
- ✅ Comprehensive activity tracking
- ✅ Client management
- ✅ API key management
- ✅ Dark mode support (coming soon)

## Tech Stack

- **React 18** - UI library
- **React Router 6** - Routing
- **Axios** - HTTP client
- **date-fns** - Date formatting
- **Recharts** - Data visualization
- **Lucide React** - Icons
- **Vite** - Build tool

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. **Install dependencies**
```bash
npm install
```

2. **Configure environment**
```bash
cp .env.example .env.development
```

Edit `.env.development`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=v1
```

3. **Start development server**
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production
```bash
npm run build
```

Build output will be in the `dist/` directory.

### Preview Production Build
```bash
npm run preview
```

## Docker Deployment

### Build Docker Image
```bash
docker build -t sentinel-frontend:latest .
```

### Run Container
```bash
docker run -d \
  --name sentinel-frontend \
  -p 3000:80 \
  -e NODE_ENV=production \
  sentinel-frontend:latest
```

### Docker Compose
```bash
docker-compose up -d
```

## Project Structure
```
src/
├── components/          # React components
│   ├── common/         # Reusable UI components
│   ├── layout/         # Layout components
│   └── features/       # Feature-specific components
├── contexts/           # React contexts
├── hooks/              # Custom React hooks
├── services/           # API services
├── utils/              # Utility functions
├── styles/             # CSS files
├── pages/              # Page components
├── App.jsx             # Main app component
├── main.jsx            # Entry point
└── router.jsx          # Route configuration
```

## Component Guidelines

### Creating New Components
```javascript
// components/features/example/ExampleComponent.jsx
import React from 'react'
import { Card, Button } from '@components/common'

const ExampleComponent = ({ data }) => {
  return (
    <Card title="Example">
      <div>{data}</div>
    </Card>
  )
}

export default ExampleComponent
```

### Using Custom Hooks
```javascript
import { useClients } from '@hooks'

const MyComponent = () => {
  const { clients, loading, error, refetch } = useClients()
  
  // Use the data
}
```

### API Calls
```javascript
import { clientsService } from '@services'

const fetchData = async () => {
  const result = await clientsService.getClients()
  if (result.success) {
    // Handle success
  }
}
```

## Styling

### CSS Variables

All colors and spacing use CSS variables defined in `globals.css`:
```css
var(--color-primary)
var(--spacing-md)
var(--radius-lg)
```

### Component Styles

Component-specific styles are in `components.css`:
```css
.btn-primary { /* styles */ }
.card { /* styles */ }
```

### Utility Classes

Utility classes in `utilities.css`:
```html
<div className="flex items-center gap-4">
  <span className="text-sm text-gray-600">Text</span>
</div>
```

## State Management

### Auth Context
```javascript
import { useAuth } from '@contexts'

const Component = () => {
  const { user, isAuthenticated, login, logout } = useAuth()
}
```

### Notification Context
```javascript
import { useNotification } from '@contexts'

const Component = () => {
  const { success, error, warning, info } = useNotification()
  
  success('Operation completed!')
}
```

## API Integration

### Configuration

API base URL is configured via environment variables:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=v1
```

### Authentication

JWT tokens are automatically attached to requests:
```javascript
// Stored in localStorage as 'sentinel_token'
// Automatically added to Authorization header
```

### Error Handling

API errors are intercepted and handled:

- 401: Redirect to login
- 403: Access forbidden
- 429: Rate limited
- 500: Server error

## Features

### Dashboard

- System statistics
- Online clients count
- Recent activity feed
- Productivity metrics

### Clients Management

- View all connected clients
- Filter by status (online/offline)
- Client details and platform info
- Activity history per client

### Activities Tracking

- Comprehensive activity log
- Filter by client, date, category
- Activity details with processes
- System metrics visualization

### API Keys

- Create and manage API keys
- Secure key display (one-time)
- Usage tracking
- Revoke keys

### Settings

- Change password
- Security settings
- Account management

## Security

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### API Key Security

- Generated with `sk_` prefix
- Only shown once upon creation
- Hashed on server
- Can be revoked anytime

### Session Management

- 24-hour token expiration
- Automatic logout on token expiry
- Secure token storage

## Performance

### Code Splitting

Pages are lazy-loaded using React.lazy():
```javascript
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'))
```

### Optimizations

- Gzip compression
- Asset caching
- Minimize bundle size
- Tree shaking

## Testing
```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## Troubleshooting

### API Connection Issues

Check that:
1. Backend is running
2. CORS is configured correctly
3. API URL is correct in `.env`

### Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Proxy Issues in Development

Vite proxy is configured in `vite.config.js`:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

## Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)

## License

Proprietary - Employee Monitoring System

## Support

For issues and questions:
- Check browser console for errors
- Review network tab for API calls
- Check backend logs

---

**Version:** 2.0.0
