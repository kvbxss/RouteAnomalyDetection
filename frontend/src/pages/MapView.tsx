import { useQuery } from "@tanstack/react-query";
import Map, { RoutePoint } from "@/components/Map";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getJSON } from "@/lib/api";

interface Flight {
  route_points?: number[][];
  latitude?: number;
  longitude?: number;
}

export default function MapView() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["flights", "sample"],
    queryFn: () =>
      getJSON<{ results: Flight[] }>("/api/flights/?page_size=1"),
  });

  let route: RoutePoint[] | undefined;
  if (data?.results?.length) {
    const f = data.results[0];
    if (Array.isArray(f.route_points) && f.route_points.length >= 2) {
      route = f.route_points.map((p: number[]) => [p[1], p[0]] as RoutePoint);
    } else if (f.latitude && f.longitude) {
      const lng = f.longitude;
      const lat = f.latitude;
      route = [
        [lng - 0.3, lat - 0.2],
        [lng, lat],
        [lng + 0.4, lat + 0.25],
      ];
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Flight Map</h1>
        <p className="text-sm text-muted-foreground">
          Visualize flight routes and anomalies on an interactive map
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Route Visualization</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="flex h-[600px] items-center justify-center">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                <span>Loading flight data...</span>
              </div>
            </div>
          )}
          {error && (
            <div className="flex h-[600px] items-center justify-center">
              <div className="text-center">
                <p className="text-sm text-destructive font-medium">
                  Failed to load flight data
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Make sure the backend is running at{" "}
                  {import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"}
                </p>
              </div>
            </div>
          )}
          {!isLoading && !error && <Map height="600px" route={route} />}
        </CardContent>
      </Card>
    </div>
  );
}
