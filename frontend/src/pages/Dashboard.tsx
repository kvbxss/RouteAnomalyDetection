import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { runDetection, trainModel, uploadCSV, getJSON } from "@/lib/api";
import { toast } from "sonner";
import { Upload, Cpu, Activity } from "lucide-react";

const Dashboard = () => {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch dashboard stats
  const { data: flightsData } = useQuery({
    queryKey: ["flights"],
    queryFn: () => getJSON<{ count: number; results: any[] }>("/api/flights/"),
  });

  const { data: anomaliesData } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () =>
      getJSON<{ count: number; results: any[] }>("/api/anomalies/"),
  });

  const totalFlights = flightsData?.count || 0;
  const totalAnomalies = anomaliesData?.count || 0;
  const highConfidence =
    anomaliesData?.results?.filter((a: any) => a.confidence_score >= 0.8)
      .length || 0;

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

  return (
    <div className="space-y-6">
      <input
        ref={fileRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={onFile}
      />

      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Monitor flight routes and anomaly detection system
        </p>
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

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-12 text-center text-muted-foreground">
            <p className="text-sm">No recent activity</p>
            <p className="text-xs mt-1">Upload flight data to get started</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
