import { useState } from 'react';
import { ScanStep } from './components/ScanStep';
import { ParseStep } from './components/ParseStep';
import { Button } from './components/ui/button';
import type { ScanResponse, ParseResponse } from './types/api';

function App() {
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [parseResult, setParseResult] = useState<ParseResponse | null>(null);
  const [resetKey, setResetKey] = useState(0);

  const handleReset = () => {
    setScanResult(null);
    setParseResult(null);
    setResetKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4">
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">CM Benchmark</h1>
              <p className="text-muted-foreground">
                Step-by-step dataset scanning and parsing workflow
              </p>
            </div>
            {(scanResult || parseResult) && (
              <Button
                variant="outline"
                onClick={handleReset}
                className="ml-4"
              >
                Reset
              </Button>
            )}
          </div>
        </header>

        <div className="space-y-6">
          <ScanStep key={resetKey} onScanComplete={setScanResult} />
          
          {scanResult && (
            <ParseStep
              key={`parse-${resetKey}`}
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

