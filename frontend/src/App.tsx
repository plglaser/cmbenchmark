import { useState } from 'react';
import { ScanStep } from './components/ScanStep';
import { ParseStep } from './components/ParseStep';
import type { ScanResponse, ParseResponse } from './types/api';

function App() {
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [parseResult, setParseResult] = useState<ParseResponse | null>(null);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">CM Benchmark</h1>
          <p className="text-muted-foreground">
            Step-by-step dataset scanning and parsing workflow
          </p>
        </header>

        <div className="space-y-6">
          <ScanStep onScanComplete={setScanResult} />
          
          {scanResult && (
            <ParseStep
              scanResult={scanResult}
              onParseComplete={setParseResult}
            />
          )}

          {/* Placeholder for future steps */}
          {parseResult && (
            <div className="p-6 border-2 border-dashed rounded-lg text-center text-muted-foreground">
              <p className="font-semibold mb-2">Step 3: Metrics (Coming Soon)</p>
              <p className="text-sm">This step will be implemented in the future</p>
            </div>
          )}

          {parseResult && (
            <div className="p-6 border-2 border-dashed rounded-lg text-center text-muted-foreground">
              <p className="font-semibold mb-2">Step 4: Report (Coming Soon)</p>
              <p className="text-sm">This step will be implemented in the future</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

