# SAP O2C Dashboard (Frontend)

This is the interactive visualization layer for the SAP Order-to-Cash Graph Query System, built with [Next.js](https://nextjs.org) and [Tailwind CSS](https://tailwindcss.com).

## 🚀 Deployment (Static Export)

As of v0.2.0, the frontend is configured for **Static Export** (`output: 'export'` in `next.config.mjs`). This allows the entire dashboard to be bundled into the FastAPI backend and served from a single port (8000).

- **Production Build**: 
  ```bash
  npm run build
  ```
  The resulting `out/` directory is served by the backend in the standalone Docker container.

## 💻 Local Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Run the development server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

3. **API Configuration**:
   The frontend automatically detects the environment. In development mode (`npm run dev`), it expects a backend at `http://localhost:8000`. In production (Docker), it uses relative paths to communicate with the same origin.

## 🌟 Visualization
We use `react-force-graph-2d` for the graph interface. If you experience performance issues with the 700+ node graph, ensure your browser has hardware acceleration enabled.

