import { useState, useRef } from 'react';
import { ScanStep } from './components/ScanStep';
import { ParseStep } from './components/ParseStep';
import { MeasureStep } from './components/MeasureStep';
import { ReportStep } from './components/ReportStep';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Upload, FileJson, X } from 'lucide-react';
import type { ScanResponse, ParseResponse, MeasureResponse } from './types/api';
import type { BenchmarkProfile } from './types/profile';

function App() {
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [parseResult, setParseResult] = useState<ParseResponse | null>(null);
  const [measureResult, setMeasureResult] = useState<MeasureResponse | null>(null);
  const [resetKey, setResetKey] = useState(0);
  const [profile, setProfile] = useState<BenchmarkProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleReset = () => {
    setScanResult(null);
    setParseResult(null);
    setMeasureResult(null);
    setResetKey((prev) => prev + 1);
  };

  const handleProfileLoad = async (file: File) => {
    try {
      const text = await file.text();
      const profileData = JSON.parse(text) as BenchmarkProfile;
      
      // Basic validation
      if (!profileData.name || !profileData.version || !profileData.output_path || !profileData.scan || !profileData.parse) {
        throw new Error('Invalid profile: missing required fields');
      }
      
      setProfile(profileData);
      setProfileError(null);
    } catch (err: any) {
      setProfileError(err.message || 'Failed to load profile');
      setProfile(null);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleProfileLoad(file);
    }
  };


  const clearProfile = () => {
    setProfile(null);
    setProfileError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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
          {/* Profile Loader */}
          <Card>
            <CardHeader>
              <CardTitle>Benchmark Profile</CardTitle>
              <CardDescription>
                Load a profile JSON file to pre-fill all parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <div className="relative">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".json"
                      onChange={handleFileInputChange}
                      className="hidden"
                      id="profile-file-input"
                      disabled={!!profile}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={!!profile}
                      className="w-full"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {profile ? 'Profile Loaded' : 'Upload Profile JSON'}
                    </Button>
                  </div>
                </div>
                {profile && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={clearProfile}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Clear
                  </Button>
                )}
              </div>
              
              {profileError && (
                <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                  {profileError}
                </div>
              )}

              {profile && (
                <div className="p-4 bg-muted rounded-md">
                  <div className="flex items-center gap-2 mb-2">
                    <FileJson className="h-4 w-4" />
                    <span className="font-semibold">Profile Loaded: {profile.name}</span>
                    <span className="text-sm text-muted-foreground">v{profile.version}</span>
                  </div>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <p>Output: <code className="font-mono">{profile.output_path}</code></p>
                    <p>Dataset: <code className="font-mono">{profile.scan.dataset_path}</code></p>
                    <p>Parser: <code className="font-mono">{profile.parse.parser_language}</code></p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <ScanStep 
            key={resetKey} 
            onScanComplete={setScanResult}
            profile={profile}
          />
          
          {scanResult && (
            <ParseStep
              key={`parse-${resetKey}`}
              onParseComplete={setParseResult}
              profile={profile}
            />
          )}

          {parseResult && (
            <MeasureStep
              key={`measure-${resetKey}`}
              onMeasureComplete={setMeasureResult}
              profile={profile}
            />
          )}

          {measureResult && (
            <ReportStep
              key={`report-${resetKey}`}
              profile={profile}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

