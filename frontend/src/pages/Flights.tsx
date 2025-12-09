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
import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadCSV, getJSON } from "@/lib/api";
import { toast } from "sonner";
import { Upload, RotateCcw, Eye, RefreshCw } from "lucide-react";
import FlightDetailModal from "@/components/FlightDetailModal";

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
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filters, setFilters] = useState({
    origin: "",
    destination: "",
    aircraft: "",
  });
  const queryClient = useQueryClient();

  const { data: flightsData, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["flights", filters],
    queryFn: () => {
      let url = "/api/flights/?page_size=100";
      if (filters.origin) url += `&departure_airport=${filters.origin}`;
      if (filters.destination) url += `&arrival_airport=${filters.destination}`;
      if (filters.aircraft) url += `&icao24=${filters.aircraft}`;
      return getJSON<{ count: number; results: Flight[] }>(url);
    },
    refetchInterval: autoRefresh ? 30000 : false, // Auto-refresh every 30 seconds
  });

  // Update last updated timestamp when data changes
  useEffect(() => {
    if (flightsData && !isLoading) {
      setLastUpdated(new Date());
    }
  }, [flightsData, isLoading]);

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

  const handleViewFlight = (flight: Flight) => {
    setSelectedFlight(flight);
    setModalOpen(true);
  };

  const handleManualRefresh = async () => {
    await refetch();
    toast.success("Data refreshed successfully");
  };

  const formatLastUpdated = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000); // seconds

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString();
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
        if (!row.first_seen) return "N/A";
        const date = new Date(row.first_seen);
        return isNaN(date.getTime()) ? "N/A" : date.toLocaleString();
      },
    },
    {
      header: "Last Seen",
      accessor: (row) => {
        if (!row.last_seen) return "N/A";
        const date = new Date(row.last_seen);
        return isNaN(date.getTime()) ? "N/A" : date.toLocaleString();
      },
    },
    {
      header: "Actions",
      accessor: (row) => (
        <Button
          variant="ghost"
          size="sm"
          className="gap-1"
          onClick={() => handleViewFlight(row)}
        >
          <Eye className="h-3 w-3" />
          View
        </Button>
      ),
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
          <div className="flex items-center justify-between">
            <CardTitle>
              Flight Records
              {flightsData?.count !== undefined && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({flightsData.count} total)
                </span>
              )}
            </CardTitle>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>Last updated: {formatLastUpdated(lastUpdated)}</span>
                {isFetching && !isLoading && (
                  <RefreshCw className="h-3 w-3 animate-spin" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-muted-foreground">Auto-refresh (30s)</span>
                </label>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1.5"
                  onClick={handleManualRefresh}
                  disabled={isFetching}
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </div>
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

      {/* Flight Detail Modal */}
      <FlightDetailModal
        flight={selectedFlight}
        open={modalOpen}
        onOpenChange={setModalOpen}
      />
    </div>
  );
};

export default Flights;
