import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, TrendingUp, AlertTriangle, Activity } from "lucide-react";

interface Anomaly {
  id: number;
  anomaly_type: string;
  confidence_score: number;
  detected_at: string;
}

interface AnomalyStatsProps {
  anomalies: Anomaly[];
}

export default function AnomalyStats({ anomalies }: AnomalyStatsProps) {
  // Calculate statistics
  const totalAnomalies = anomalies.length;

  const highConfidence = anomalies.filter(a => a.confidence_score >= 0.8).length;
  const mediumConfidence = anomalies.filter(a => a.confidence_score >= 0.5 && a.confidence_score < 0.8).length;
  const lowConfidence = anomalies.filter(a => a.confidence_score < 0.5).length;

  const typeBreakdown = anomalies.reduce((acc, anomaly) => {
    acc[anomaly.anomaly_type] = (acc[anomaly.anomaly_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const avgConfidence = totalAnomalies > 0
    ? (anomalies.reduce((sum, a) => sum + a.confidence_score, 0) / totalAnomalies * 100).toFixed(1)
    : 0;

  // Get type colors
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'altitude_anomaly': 'bg-red-500',
      'speed_anomaly': 'bg-orange-500',
      'route_deviation': 'bg-yellow-500',
      'temporal_anomaly': 'bg-blue-500',
      'combined': 'bg-purple-500',
    };
    return colors[type] || 'bg-gray-500';
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'altitude_anomaly': 'Altitude',
      'speed_anomaly': 'Speed',
      'route_deviation': 'Route',
      'temporal_anomaly': 'Temporal',
      'combined': 'Combined',
    };
    return labels[type] || type;
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Anomalies */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Anomalies</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalAnomalies}</div>
          <p className="text-xs text-muted-foreground mt-1">
            Detected anomalies
          </p>
        </CardContent>
      </Card>

      {/* Average Confidence */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{avgConfidence}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            Average detection confidence
          </p>
        </CardContent>
      </Card>

      {/* High Confidence */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">High Confidence</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">{highConfidence}</div>
          <p className="text-xs text-muted-foreground mt-1">
            ≥ 80% confidence
          </p>
        </CardContent>
      </Card>

      {/* By Type */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">By Type</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{Object.keys(typeBreakdown).length}</div>
          <p className="text-xs text-muted-foreground mt-1">
            Unique anomaly types
          </p>
        </CardContent>
      </Card>

      {/* Type Breakdown - Full Width */}
      <Card className="md:col-span-2 lg:col-span-4">
        <CardHeader>
          <CardTitle className="text-sm">Anomaly Type Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.keys(typeBreakdown).length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-20" />
              <p className="text-sm">No data available</p>
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(typeBreakdown)
                .sort((a, b) => b[1] - a[1])
                .map(([type, count]) => {
                  const percentage = ((count / totalAnomalies) * 100).toFixed(1);
                  return (
                    <div key={type} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{getTypeLabel(type)}</span>
                        <span className="text-muted-foreground">
                          {count} ({percentage}%)
                        </span>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getTypeColor(type)} transition-all`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Confidence Distribution */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm">Confidence Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-red-600">High (≥80%)</span>
                <span className="text-muted-foreground">{highConfidence}</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all"
                  style={{ width: totalAnomalies > 0 ? `${(highConfidence / totalAnomalies) * 100}%` : '0%' }}
                />
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-yellow-600">Medium (50-79%)</span>
                <span className="text-muted-foreground">{mediumConfidence}</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-yellow-500 transition-all"
                  style={{ width: totalAnomalies > 0 ? `${(mediumConfidence / totalAnomalies) * 100}%` : '0%' }}
                />
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-blue-600">Low (&lt;50%)</span>
                <span className="text-muted-foreground">{lowConfidence}</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all"
                  style={{ width: totalAnomalies > 0 ? `${(lowConfidence / totalAnomalies) * 100}%` : '0%' }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
