import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

const Anomalies = () => {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold tracking-widest uppercase">
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
              <Select defaultValue="0.1">
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
              <Label htmlFor="model-version">Model Version</Label>
              <Select defaultValue="latest">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="latest">Latest (v1.0.0)</SelectItem>
                  <SelectItem value="stable">Stable (v0.9.0)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button className="w-full">Train Model</Button>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">Run Detection</Button>
            <Button variant="outline">View Statistics</Button>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Anomaly Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div>
              <Label htmlFor="anomaly-type">Anomaly Type</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="route_deviation">
                    Route Deviation
                  </SelectItem>
                  <SelectItem value="speed_anomaly">Speed Anomaly</SelectItem>
                  <SelectItem value="altitude_anomaly">
                    Altitude Anomaly
                  </SelectItem>
                  <SelectItem value="temporal_anomaly">
                    Temporal Anomaly
                  </SelectItem>
                  <SelectItem value="combined">Combined</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="confidence-min">Min Confidence</Label>
              <Select defaultValue="0.0">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0.0">Any (0.0+)</SelectItem>
                  <SelectItem value="0.5">Medium (0.5+)</SelectItem>
                  <SelectItem value="0.8">High (0.8+)</SelectItem>
                  <SelectItem value="0.9">Very High (0.9+)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="review-status">Review Status</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pending">Pending Review</SelectItem>
                  <SelectItem value="reviewed">Reviewed</SelectItem>
                  <SelectItem value="false_positive">False Positive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button variant="outline" className="w-full">
                Apply Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Anomaly List */}
      <Card>
        <CardHeader>
          <CardTitle>Detected Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-center text-muted-foreground">
            <p>No anomalies detected</p>
            <p className="text-xs">
              Train the model and run detection to find anomalies
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Anomalies;
