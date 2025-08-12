import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRef, useState } from "react";
import { runDetection, trainModel, uploadCSV } from "@/lib/api";

const Label = ({ children }: { children: React.ReactNode }) => (
  <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
    {children}
  </span>
);

const Dashboard = () => {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const onPickFile = () => fileRef.current?.click();
  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[1] ?? e.target.files?.[0];
    if (!f) return;
    setBusy("upload");
    try {
      await uploadCSV(f);
      alert("CSV uploaded and processed.");
    } catch (err: any) {
      alert(err?.message || "Upload failed");
    } finally {
      setBusy(null);
      e.target.value = "";
    }
  };

  const onTrain = async () => {
    setBusy("train");
    try {
      const res = await trainModel({ contamination: 0.15, save_model: false });
      alert(`Trained model on ${res.training_samples ?? "?"} samples`);
    } catch (err: any) {
      alert(err?.message || "Training failed");
    } finally {
      setBusy(null);
    }
  };

  const onDetect = async () => {
    setBusy("detect");
    try {
      const res = await runDetection({ retrain: false });
      const count = res.total_anomalies_detected ?? res.anomalies_detected ?? 0;
      alert(`Detection complete. Anomalies: ${count}`);
    } catch (err: any) {
      alert(err?.message || "Detection failed");
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
        <h1 className="text-xl font-semibold tracking-widest uppercase">
          Dashboard
        </h1>
        <p className="text-sm text-muted-foreground">
          Overview of flight routes and anomaly detection system
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Flights</CardTitle>
            <Label>stats</Label>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">
              No flights loaded yet
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Anomalies Detected
            </CardTitle>
            <Label>monitor</Label>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">No anomalies found</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              High Confidence
            </CardTitle>
            <Label>confidence</Label>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">
              No high confidence alerts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Label>online</Label>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">Online</div>
            <p className="text-xs text-muted-foreground">
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
          <div className="grid gap-2 md:grid-cols-3">
            <Button
              variant="outline"
              className="justify-start"
              onClick={onPickFile}
              disabled={busy !== null}
            >
              Upload Flight Data
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={onTrain}
              disabled={busy !== null}
            >
              Train ML Model
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={onDetect}
              disabled={busy !== null}
            >
              Run Detection
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
          <div className="py-8 text-center text-muted-foreground">
            <p>No recent activity</p>
            <p className="text-xs">Upload some flight data to get started</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
