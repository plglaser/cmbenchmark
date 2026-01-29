# CM Benchmark Frontend

React + Vite + TypeScript frontend for the CM Benchmark tool.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Building

To build for production:
```bash
npm run build
```

## Features

- Step-by-step workflow for dataset processing
- Scan dataset directory for model files
- Parse models using various parsers
- Extensible architecture for future steps (measure, report)

## Tech Stack

- React 18
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui components
- Axios for API calls
- Zod for validation

