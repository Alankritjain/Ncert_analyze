# NCERT Analyzer - Frontend

A modern, research-grade React + Vite frontend for analyzing JEE MAINS and NEET exam questions using machine learning predictions.

## 🚀 Tech Stack

- **Framework**: React 19
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS
- **Routing**: React Router v7
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Icons**: Lucide React

## 📋 Features

### 5 Main Pages

1. **Dashboard Overview**
   - Key performance metrics (chapters analyzed, questions reviewed, accuracy, progress)
   - Recent activity feed
   - Study tips and exam information

2. **Chapter Importance Analyzer**
   - Bar chart showing importance ranking of chapters
   - Chapter details table with importance scores
   - Filter by exam type (JEE MAINS / NEET)

3. **Question Alignment Checker**
   - Analyze question-to-chapter alignment
   - Scatter plot showing chapter-wise alignment
   - Detailed recommendations and misaligned topics

4. **Trend Analytics**
   - Line charts for accuracy progress over time
   - Performance trends and comprehensive learning timeline
   - Monthly detailed report with trends

5. **Study Recommendation Engine**
   - Personalized study plan generation
   - Weekly schedule with topic breakdown
   - Priority topics with mastery tracking
   - Success probability prediction

## 🛠️ Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Backend Flask API running on `http://localhost:5000`

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   cp .env.example .env.local
   ```

4. **Update `.env.local` if needed:**
   ```env
   VITE_API_BASE_URL=http://localhost:5000
   VITE_APP_NAME=NCERT Analyzer
   ```

### Running the Application

**Development Mode:**
```bash
npm run dev
```
The app will be available at `http://localhost:5173`

**Production Build:**
```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable components
│   │   ├── Sidebar.jsx      # Navigation sidebar
│   │   ├── Header.jsx       # Page header with breadcrumbs
│   │   ├── Card.jsx         # Generic card component
│   │   └── StatCard.jsx     # Statistics card component
│   ├── pages/               # Page components
│   │   ├── Dashboard.jsx
│   │   ├── ChapterImportance.jsx
│   │   ├── QuestionAlignment.jsx
│   │   ├── TrendAnalytics.jsx
│   │   └── StudyRecommendation.jsx
│   ├── services/            # API integration
│   │   └── api.js          # Axios API client with endpoints
│   ├── styles/              # Additional styles
│   ├── App.jsx              # Main app component with routing
│   ├── App.css              # App-specific styles
│   ├── index.css            # Global + Tailwind CSS
│   └── main.jsx             # React entry point
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🎨 Design System

### Color Palette
- **Primary**: Blue (`#0284c7`)
- **Secondary**: Light Blue
- **Accent**: Purple (`#8b5cf6`)
- **Success**: Green
- **Warning**: Yellow
- **Error**: Red

### Components
- **Cards**: White background with subtle shadow and border
- **Buttons**: Primary color with hover effects
- **Typography**: Clear hierarchy with responsive sizes
- **Responsive Design**: Mobile-first approach with Tailwind breakpoints

## 📡 API Integration

All API calls are managed through `src/services/api.js`. The frontend communicates with the Flask backend using the following endpoints:

- `POST /api/predict_alignment` - Predict question alignment
- `GET /api/chapter_importance` - Get chapter importance analysis
- `GET /api/trend_analysis` - Get trend data
- `POST /api/study_plan` - Generate personalized study plan

**Mock Data**: The frontend includes mock data as fallbacks for development and testing.

## 🧩 Key Components

### Sidebar.jsx
- Responsive navigation drawer
- Mobile hamburger menu
- Active route highlighting
- Collapsible on mobile

### Header.jsx
- Dynamic page titles based on current route
- Exam information display
- Breadcrumb navigation

### StatCard.jsx
- KPI display with icons
- Trend indicators (up/down)
- Flexible styling

## 📊 Charts & Visualizations

Using Recharts for responsive, interactive charts:
- **BarChart**: Chapter importance rankings
- **LineChart**: Accuracy trends over time
- **AreaChart**: Filled area charts with gradients
- **ScatterChart**: Question alignment visualization

All charts are responsive and work seamlessly on mobile and desktop.

## 🔧 Customization

### Adding New Pages

1. Create a new file in `src/pages/YourPage.jsx`
2. Add import and route in `src/App.jsx`
3. Add menu item in `src/components/Sidebar.jsx`

### Styling

- Use Tailwind CSS utilities for styling
- Extend theme in `tailwind.config.js` for custom colors/fonts
- Global styles in `src/index.css`

### API Integration

Update endpoints in `src/services/api.js` to match backend URLs.

## 🌐 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://localhost:5000` | Backend API URL |
| `VITE_APP_NAME` | `NCERT Analyzer` | Application title |

## 🚨 Common Issues

### API Connection Failing
- Ensure backend is running on port 5000
- Check CORS is enabled in Flask app
- Verify `.env.local` has correct `VITE_API_BASE_URL`

### Charts Not Rendering
- Verify mock data is being returned if API fails
- Check browser console for errors
- Ensure Recharts is properly installed

### Styling Issues
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Rebuild Tailwind CSS: `npm run build`

## 📈 Performance Tips

- Charts lazy load with skeleton loading states
- Images optimized using Vite's asset handling
- Code splitting via React Router
- Responsive images for faster mobile loads

## 🛠️ Development Tools

- **Linting**: ESLint configured
- **Code Formatting**: Compatible with Prettier
- **Hot Module Replacement**: Built-in Vite HMR

## 📝 Notes

- Frontend is a SPA (Single Page Application)
- All data fetching is from the Flask backend API
- Responsive design supports mobile, tablet, and desktop
- Dark mode can be added by extending Tailwind config

## 📚 Resources

- [React Documentation](https://react.dev)
- [Vite Guide](https://vite.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Recharts](https://recharts.org)
- [React Router](https://reactrouter.com)

---

**Built for research-grade NCERT exam analysis** 🎓
