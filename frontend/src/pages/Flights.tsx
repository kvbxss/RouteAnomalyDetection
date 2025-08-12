import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";
import { uploadCSV } from "@/lib/api";

const Flights = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const onUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const res = await uploadCSV(file);
      setResult(res);
    } catch (e: any) {
      setError(e?.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold tracking-widest uppercase">
          Flight Management
        </h1>
        <p className="text-sm text-muted-foreground">
          Upload, view, and manage flight data
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Flight Data</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="file-upload">CSV File</Label>
              <Input
                id="file-upload"
                type="file"
                accept=".csv"
                className="mt-1"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
            <div>
              <Label htmlFor="data-source">Data Source</Label>
              <Select defaultValue="csv">
                <SelectTrigger>
                  <SelectValue placeholder="Select data source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV Upload</SelectItem>
                  <SelectItem value="api">API Endpoint</SelectItem>
                  <SelectItem value="realtime">Real-time Feed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              className="w-full md:w-auto"
              onClick={onUpload}
              disabled={!file || uploading}
            >
              {uploading ? "Uploading..." : "📁 Upload and Process"}
            </Button>
            {error && <span className="text-sm text-red-400">{error}</span>}
          </div>
          {result && (
            <div className="text-sm text-muted-foreground">
              <div>Processed: {result.processed_count}</div>
              <div>Errors: {result.error_count}</div>
              <div>Warnings: {result.warning_count}</div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <Label htmlFor="origin">Origin</Label>
              <Input id="origin" placeholder="e.g., LAX" />
            </div>
            <div>
              <Label htmlFor="destination">Destination</Label>
              <Input id="destination" placeholder="e.g., JFK" />
            </div>
            <div>
              <Label htmlFor="date-range">Date</Label>
              <Input id="date-range" type="date" />
            </div>
            <div>
              <Label htmlFor="aircraft">Aircraft ID</Label>
              <Input id="aircraft" placeholder="e.g., N12345" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Flight List */}
      <Card>
        <CardHeader>
          <CardTitle>Flight Records</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-center text-muted-foreground">
            <p>No flights found</p>
            <p className="text-xs">Upload some flight data to get started</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Flights;
