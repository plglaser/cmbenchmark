import { useState } from 'react';
import { ScanStep } from './components/ScanStep';
import { ParseStep } from './components/ParseStep';
import { MeasureStep } from './components/MeasureStep';
import { ReportStep } from './components/ReportStep';
import { Button } from './components/ui/button';
import type { ScanResponse, ParseResponse, MeasureResponse } from './types/api';

function App() {
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [parseResult, setParseResult] = useState<ParseResponse | null>(null);
  const [measureResult, setMeasureResult] = useState<MeasureResponse | null>(null);
  const [resetKey, setResetKey] = useState(0);

  const handleReset = () => {
    setScanResult(null);
    setParseResult(null);
    setMeasureResult(null);
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
                Step-by-step dataset benchmarking
              </p>
            </div>
            {(scanResult || parseResult || measureResult) && (
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

          {parseResult && (
            <MeasureStep
              key={`measure-${resetKey}`}
              parseResult={parseResult}
              onMeasureComplete={setMeasureResult}
            />
          )}

          {measureResult && (
            <ReportStep
              key={`report-${resetKey}`}
              measureResult={measureResult}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

