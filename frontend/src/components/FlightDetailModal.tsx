import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Map, { RoutePoint } from "@/components/Map";
import { Plane, MapPin, Clock, AlertTriangle, TrendingUp, Activity } from "lucide-react";

interface Flight {
  id: number;
  flight_id: string;
  aircraft_id?: string;
  icao24?: string;
  departure_airport?: string;
  arrival_airport?: string;
  origin?: string;
  destination?: string;
  first_seen?: string;
  last_seen?: string;
  timestamp?: string;
  latitude?: number;
  longitude?: number;
  altitude?: number;
  speed?: number;
  heading?: number;
  route_points?: number[][];
  route_geometry?: any;
}

interface Anomaly {
  id: number;
  anomaly_type: string;
  confidence_score: number;
  detected_at: string;
  anomaly_details?: any;
}

interface FlightDetailModalProps {
  flight: Flight | null;
  anomalies?: Anomaly[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function FlightDetailModal({ flight, anomalies = [], open, onOpenChange }: FlightDetailModalProps) {
  if (!flight) return null;

  // Prepare route data for map
  let route: RoutePoint[] | undefined;
  if (flight.route_points && Array.isArray(flight.route_points) && flight.route_points.length >= 2) {
    route = flight.route_points.map((p: number[]) => [p[1], p[0]] as RoutePoint);
  } else if (flight.latitude && flight.longitude) {
    route = [[flight.longitude, flight.latitude]] as RoutePoint[];
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatNumber = (num?: number, decimals: number = 2) => {
    if (num === undefined || num === null) return 'N/A';
    return num.toFixed(decimals);
  };

  const getAnomalyTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'altitude_anomaly': 'text-red-600',
      'speed_anomaly': 'text-orange-600',
      'route_deviation': 'text-yellow-600',
      'temporal_anomaly': 'text-blue-600',
      'combined': 'text-purple-600',
    };
    return colors[type] || 'text-gray-600';
  };

  const getAnomalyTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'altitude_anomaly': 'Altitude Anomaly',
      'speed_anomaly': 'Speed Anomaly',
      'route_deviation': 'Route Deviation',
      'temporal_anomaly': 'Temporal Anomaly',
      'combined': 'Combined Anomaly',
    };
    return labels[type] || type;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plane className="h-5 w-5" />
            Flight {flight.flight_id}
          </DialogTitle>
          <DialogDescription>
            Comprehensive flight information and route details
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Flight Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Basic Info */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Plane className="h-4 w-4" />
                  Flight Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Flight ID:</span>
                  <span className="font-medium">{flight.flight_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Aircraft:</span>
                  <span className="font-medium">{flight.aircraft_id || flight.icao24 || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Origin:</span>
                  <span className="font-medium">{flight.departure_airport || flight.origin || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Destination:</span>
                  <span className="font-medium">{flight.arrival_airport || flight.destination || 'N/A'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Position & Time */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Position & Timing
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">First Seen:</span>
                  <span className="font-medium text-xs">{formatDateTime(flight.first_seen || flight.timestamp)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last Seen:</span>
                  <span className="font-medium text-xs">{formatDateTime(flight.last_seen)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Latitude:</span>
                  <span className="font-medium">{formatNumber(flight.latitude, 6)}°</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Longitude:</span>
                  <span className="font-medium">{formatNumber(flight.longitude, 6)}°</span>
                </div>
              </CardContent>
            </Card>

            {/* Flight Data */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Flight Data
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Altitude:</span>
                  <span className="font-medium">{formatNumber(flight.altitude, 0)} ft</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Speed:</span>
                  <span className="font-medium">{formatNumber(flight.speed, 1)} kts</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Heading:</span>
                  <span className="font-medium">{formatNumber(flight.heading, 0)}°</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Route Points:</span>
                  <span className="font-medium">{route?.length || 0}</span>
                </div>
              </CardContent>
            </Card>

            {/* Anomalies */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Anomaly Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {anomalies.length === 0 ? (
                  <div className="text-center py-4 text-muted-foreground">
                    <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-xs">No anomalies detected</p>
                  </div>
                ) : (
                  anomalies.map((anomaly, idx) => (
                    <div key={idx} className="border-l-2 border-orange-500 pl-3 py-2 bg-orange-50/50 dark:bg-orange-950/20 rounded-r">
                      <div className="flex justify-between items-start mb-1">
                        <span className={`font-medium ${getAnomalyTypeColor(anomaly.anomaly_type)}`}>
                          {getAnomalyTypeLabel(anomaly.anomaly_type)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {(anomaly.confidence_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Detected: {formatDateTime(anomaly.detected_at)}
                      </p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Map */}
          {route && route.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  Flight Route
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Map height="400px" route={route} />
              </CardContent>
            </Card>
          )}

          {/* Anomaly Details */}
          {anomalies.length > 0 && anomalies[0].anomaly_details && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Anomaly Details</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                  {JSON.stringify(anomalies[0].anomaly_details, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
