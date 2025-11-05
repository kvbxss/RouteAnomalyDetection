import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DataTable, Column } from "@/components/ui/data-table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { trainModel, runDetection, getJSON } from "@/lib/api";
import { toast } from "sonner";
import { Cpu, Activity, BarChart3 } from "lucide-react";

interface Anomaly {
  id: number;
  flight: {
    flight_id: string;
    departure_airport: string;
    arrival_airport: string;
  };
  anomaly_type: string;
  confidence_score: number;
  detected_at: string;
}

const Anomalies = () => {
  const [training, setTraining] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [contamination, setContamination] = useState("0.1");
  const queryClient = useQueryClient();

  const { data: anomaliesData, isLoading } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () =>
      getJSON<{ count: number; results: Anomaly[] }>("/api/anomalies/"),
  });

  const anomalies = anomaliesData?.results || [];

  const handleTrain = async () => {
    setTraining(true);
    const toastId = toast.loading("Training ML model...");

    try {
      const res: any = await trainModel({
        contamination: parseFloat(contamination),
        save_model: true,
      });
      toast.success(
        `Model trained on ${res.training_samples ?? "?"} samples`,
        { id: toastId }
      );
    } catch (err: any) {
      toast.error(err?.message || "Training failed", { id: toastId });
    } finally {
      setTraining(false);
    }
  };

  const handleDetect = async () => {
    setDetecting(true);
    const toastId = toast.loading("Running anomaly detection...");

    try {
      const res: any = await runDetection({ retrain: false });
      const count = res.total_anomalies_detected ?? res.anomalies_detected ?? 0;
      toast.success(`Detected ${count} anomalies`, { id: toastId });
      queryClient.invalidateQueries({ queryKey: ["anomalies"] });
    } catch (err: any) {
      toast.error(err?.message || "Detection failed", { id: toastId });
    } finally {
      setDetecting(false);
    }
  };

  const columns: Column<Anomaly>[] = [
    {
      header: "Flight ID",
      accessor: (row) => row.flight?.flight_id || "N/A",
      className: "font-medium",
    },
    {
      header: "Route",
      accessor: (row) =>
        `${row.flight?.departure_airport || "?"} → ${row.flight?.arrival_airport || "?"}`,
    },
    {
      header: "Type",
      accessor: "anomaly_type",
    },
    {
      header: "Confidence",
      accessor: (row) => {
        const confidence = row.confidence_score;
        const percentage = (confidence * 100).toFixed(1);
        const color =
          confidence >= 0.8
            ? "text-red-600"
            : confidence >= 0.5
              ? "text-yellow-600"
              : "text-muted-foreground";
        return (
          <span className={`font-medium ${color}`}>{percentage}%</span>
        );
      },
    },
    {
      header: "Detected At",
      accessor: (row) => {
        const date = new Date(row.detected_at);
        return date.toLocaleString();
      },
    },
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          Anomaly Detection
        </h1>
        <p className="text-sm text-muted-foreground">
          View and manage detected flight anomalies
        </p>
      </div>

      {/* ML Model Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Machine Learning Model</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="contamination">Contamination</Label>
              <Select
                value={contamination}
                onValueChange={setContamination}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0.05">5% (Conservative)</SelectItem>
                  <SelectItem value="0.1">10% (Balanced)</SelectItem>
                  <SelectItem value="0.15">15% (Aggressive)</SelectItem>
                  <SelectItem value="0.2">20% (Very Aggressive)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="model-version">Model Algorithm</Label>
              <Select defaultValue="isolation-forest">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="isolation-forest">
                    Isolation Forest
                  </SelectItem>
                  <SelectItem value="one-class-svm" disabled>
                    One-Class SVM
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                className="w-full gap-2"
                onClick={handleTrain}
                disabled={training || detecting}
              >
                <Cpu className="h-4 w-4" />
                {training ? "Training..." : "Train Model"}
              </Button>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="gap-2"
              onClick={handleDetect}
              disabled={training || detecting}
            >
              <Activity className="h-4 w-4" />
              {detecting ? "Detecting..." : "Run Detection"}
            </Button>
            <Button variant="outline" className="gap-2" disabled>
              <BarChart3 className="h-4 w-4" />
              View Statistics
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Anomaly List */}
      <Card>
        <CardHeader>
          <CardTitle>
            Detected Anomalies
            {anomaliesData?.count !== undefined && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({anomaliesData.count} total)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={anomalies}
            columns={columns}
            loading={isLoading}
            emptyMessage="No anomalies detected. Train the model and run detection to find anomalies."
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default Anomalies;
