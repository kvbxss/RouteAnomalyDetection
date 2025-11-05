import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DataTable, Column } from "@/components/ui/data-table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadCSV, getJSON } from "@/lib/api";
import { toast } from "sonner";
import { Upload, RotateCcw } from "lucide-react";

interface Flight {
  id: number;
  flight_id: string;
  icao24: string;
  departure_airport: string;
  arrival_airport: string;
  first_seen: string;
  last_seen: string;
  route_geometry: any;
}

const Flights = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [filters, setFilters] = useState({
    origin: "",
    destination: "",
    aircraft: "",
  });
  const queryClient = useQueryClient();

  const { data: flightsData, isLoading } = useQuery({
    queryKey: ["flights", filters],
    queryFn: () => {
      let url = "/api/flights/?page_size=100";
      if (filters.origin) url += `&departure_airport=${filters.origin}`;
      if (filters.destination) url += `&arrival_airport=${filters.destination}`;
      if (filters.aircraft) url += `&icao24=${filters.aircraft}`;
      return getJSON<{ count: number; results: Flight[] }>(url);
    },
  });

  const flights = flightsData?.results || [];

  const onUpload = async () => {
    if (!file) return;
    setUploading(true);
    const toastId = toast.loading("Uploading and processing CSV...");

    try {
      const res = await uploadCSV(file);
      toast.success(
        `Processed ${res.processed_count} flights successfully`,
        { id: toastId }
      );
      setFile(null);
      queryClient.invalidateQueries({ queryKey: ["flights"] });
    } catch (e: any) {
      toast.error(e?.message || "Upload failed", { id: toastId });
    } finally {
      setUploading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({ origin: "", destination: "", aircraft: "" });
  };

  const columns: Column<Flight>[] = [
    {
      header: "Flight ID",
      accessor: "flight_id",
      className: "font-medium",
    },
    {
      header: "Aircraft",
      accessor: "icao24",
    },
    {
      header: "Origin",
      accessor: "departure_airport",
    },
    {
      header: "Destination",
      accessor: "arrival_airport",
    },
    {
      header: "First Seen",
      accessor: (row) => {
        const date = new Date(row.first_seen);
        return date.toLocaleString();
      },
    },
    {
      header: "Last Seen",
      accessor: (row) => {
        const date = new Date(row.last_seen);
        return date.toLocaleString();
      },
    },
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
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
          <Button
            className="gap-2"
            onClick={onUpload}
            disabled={!file || uploading}
          >
            <Upload className="h-4 w-4" />
            {uploading ? "Uploading..." : "Upload and Process"}
          </Button>
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
              <Input
                id="origin"
                placeholder="e.g., KJFK"
                value={filters.origin}
                onChange={(e) => handleFilterChange("origin", e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="destination">Destination</Label>
              <Input
                id="destination"
                placeholder="e.g., KLAX"
                value={filters.destination}
                onChange={(e) =>
                  handleFilterChange("destination", e.target.value)
                }
              />
            </div>
            <div>
              <Label htmlFor="aircraft">Aircraft ID</Label>
              <Input
                id="aircraft"
                placeholder="e.g., a12345"
                value={filters.aircraft}
                onChange={(e) =>
                  handleFilterChange("aircraft", e.target.value)
                }
              />
            </div>
            <div className="flex items-end gap-2">
              <Button
                variant="outline"
                className="flex-1 gap-2"
                onClick={clearFilters}
              >
                <RotateCcw className="h-4 w-4" />
                Reset
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Flight List */}
      <Card>
        <CardHeader>
          <CardTitle>
            Flight Records
            {flightsData?.count !== undefined && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({flightsData.count} total)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={flights}
            columns={columns}
            loading={isLoading}
            emptyMessage="No flights found. Upload flight data to get started."
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default Flights;
