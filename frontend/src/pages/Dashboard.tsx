import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRef, useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { runDetection, trainModel, uploadCSV, getJSON } from "@/lib/api";
import { toast } from "sonner";
import { Upload, Cpu, Activity, RefreshCw, MapPin } from "lucide-react";
import Map, { AnomalyMarker } from "@/components/Map";
import FlightDetailModal from "@/components/FlightDetailModal";

interface Anomaly {
  id: number;
  flight: {
    id: number;
    flight_id: string;
    departure_airport: string;
    arrival_airport: string;
    route_geometry: any;
  };
  anomaly_type: string;
  confidence_score: number;
  detected_at: string;
  details: any;
}

const Dashboard = () => {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [selectedFlight, setSelectedFlight] = useState<any | null>(null);
  const [selectedAnomalies, setSelectedAnomalies] = useState<Anomaly[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const queryClient = useQueryClient();

  // Fetch dashboard stats
  const { data: flightsData, isFetching: fetchingFlights, refetch: refetchFlights } = useQuery({
    queryKey: ["flights"],
    queryFn: () => getJSON<{ count: number; results: any[] }>("/api/flights/?page_size=100"),
    refetchInterval: autoRefresh ? 30000 : false,
  });

  const { data: anomaliesData, isFetching: fetchingAnomalies, refetch: refetchAnomalies } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () =>
      getJSON<{ count: number; results: Anomaly[] }>("/api/anomalies/"),
    refetchInterval: autoRefresh ? 30000 : false,
  });

  const totalFlights = flightsData?.count || 0;
  const totalAnomalies = anomaliesData?.count || 0;
  const anomalies = anomaliesData?.results || [];
  const highConfidence = anomalies.filter(a => a.confidence_score >= 0.8).length;

  // Update last updated timestamp
  useEffect(() => {
    if (flightsData && anomaliesData) {
      setLastUpdated(new Date());
    }
  }, [flightsData, anomaliesData]);

  const onPickFile = () => fileRef.current?.click();

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    setBusy("upload");
    const toastId = toast.loading("Uploading CSV file...");

    try {
      const result = await uploadCSV(f);
      toast.success(
        `Successfully processed ${result.processed_count} flights`,
        { id: toastId }
      );
      queryClient.invalidateQueries({ queryKey: ["flights"] });
    } catch (err: any) {
      toast.error(err?.message || "Upload failed", { id: toastId });
    } finally {
      setBusy(null);
      e.target.value = "";
    }
  };

  const onTrain = async () => {
    setBusy("train");
    const toastId = toast.loading("Training ML model...");

    try {
      const res: any = await trainModel({ contamination: 0.15, save_model: false });
      toast.success(
        `Model trained on ${res.training_samples ?? "?"} samples`,
        { id: toastId }
      );
    } catch (err: any) {
      toast.error(err?.message || "Training failed", { id: toastId });
    } finally {
      setBusy(null);
    }
  };

  const onDetect = async () => {
    setBusy("detect");
    const toastId = toast.loading("Running anomaly detection...");

    try {
      const res: any = await runDetection({ retrain: false });
      const count = res.total_anomalies_detected ?? res.anomalies_detected ?? 0;
      toast.success(`Detected ${count} anomalies`, { id: toastId });
      queryClient.invalidateQueries({ queryKey: ["anomalies"] });
    } catch (err: any) {
      toast.error(err?.message || "Detection failed", { id: toastId });
    } finally {
      setBusy(null);
    }
  };

  const handleManualRefresh = async () => {
    await Promise.all([refetchFlights(), refetchAnomalies()]);
    toast.success("Dashboard data refreshed");
  };

  const formatLastUpdated = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString();
  };

  // Convert anomalies to map markers
  const anomalyMarkers: AnomalyMarker[] = anomalies
    .filter(a => {
      const geometry = a.flight?.route_geometry;
      if (!geometry) return false;
      if (geometry.type === "LineString" && geometry.coordinates?.length > 0) {
        return true;
      }
      return false;
    })
    .map(a => {
      const geometry = a.flight.route_geometry;
      const position = geometry.coordinates[0] as [number, number];

      return {
        id: a.id,
        position,
        type: a.anomaly_type,
        confidence: a.confidence_score,
        flightId: a.flight.flight_id,
      };
    });

  const handleMarkerClick = (marker: AnomalyMarker) => {
    const anomaly = anomalies.find(a => a.id === marker.id);
    if (anomaly) {
      setSelectedFlight(anomaly.flight);
      setSelectedAnomalies([anomaly]);
      setModalOpen(true);
    }
  };

  const isFetching = fetchingFlights || fetchingAnomalies;

  return (
    <div className="space-y-6">
      <input
        ref={fileRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={onFile}
      />

      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Monitor flight routes and anomaly detection system
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Last updated: {formatLastUpdated(lastUpdated)}</span>
            {isFetching && <RefreshCw className="h-3 w-3 animate-spin" />}
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

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Flights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalFlights}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {totalFlights === 0 ? "No flights loaded" : "Flight records"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Anomalies Detected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalAnomalies}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {totalAnomalies === 0 ? "No anomalies found" : "Total detected"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              High Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{highConfidence}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Confidence ≥ 0.8
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <div className="text-3xl font-bold">Online</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              All systems operational
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <Button
              variant="outline"
              className="justify-start gap-2 h-auto py-3"
              onClick={onPickFile}
              disabled={busy !== null}
            >
              <Upload className="h-4 w-4" />
              <div className="flex flex-col items-start">
                <span className="font-medium">Upload Flight Data</span>
                <span className="text-xs text-muted-foreground">
                  Import CSV file
                </span>
              </div>
            </Button>

            <Button
              variant="outline"
              className="justify-start gap-2 h-auto py-3"
              onClick={onTrain}
              disabled={busy !== null}
            >
              <Cpu className="h-4 w-4" />
              <div className="flex flex-col items-start">
                <span className="font-medium">Train ML Model</span>
                <span className="text-xs text-muted-foreground">
                  {busy === "train" ? "Training..." : "Isolation Forest"}
                </span>
              </div>
            </Button>

            <Button
              variant="outline"
              className="justify-start gap-2 h-auto py-3"
              onClick={onDetect}
              disabled={busy !== null}
            >
              <Activity className="h-4 w-4" />
              <div className="flex flex-col items-start">
                <span className="font-medium">Run Detection</span>
                <span className="text-xs text-muted-foreground">
                  {busy === "detect" ? "Detecting..." : "Analyze routes"}
                </span>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Interactive Map */}
      <Card>
        <CardHeader>
          <CardTitle>Flight Routes & Anomalies</CardTitle>
          <p className="text-sm text-muted-foreground">
            Click on anomaly markers to view flight details
          </p>
        </CardHeader>
        <CardContent>
          {anomalyMarkers.length === 0 ? (
            <div className="flex items-center justify-center h-[500px] bg-muted/20 rounded-lg">
              <div className="flex flex-col items-center gap-3 text-center max-w-md">
                <MapPin className="h-12 w-12 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">No anomalies to display</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Upload flight data and run anomaly detection to see results on the map
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <Map
              height="500px"
              anomalyMarkers={anomalyMarkers}
              onMarkerClick={handleMarkerClick}
            />
          )}
        </CardContent>
      </Card>

      {/* Flight Detail Modal */}
      <FlightDetailModal
        flight={selectedFlight}
        anomalies={selectedAnomalies}
        open={modalOpen}
        onOpenChange={setModalOpen}
      />
    </div>
  );
};

export default Dashboard;
