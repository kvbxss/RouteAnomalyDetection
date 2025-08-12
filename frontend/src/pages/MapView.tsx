import { useQuery } from "@tanstack/react-query";
import Map, { RoutePoint } from "@/components/Map";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

async function fetchFlights() {
  const res = await fetch("http://127.0.0.1:8000/api/flights/?page_size=1");
  if (!res.ok) throw new Error("Failed to fetch flights");
  return res.json();
}

export default function MapView() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["flights", "sample"],
    queryFn: fetchFlights,
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
        <h1 className="text-xl font-semibold tracking-widest uppercase">
          Flight Map
        </h1>
        <p className="text-sm text-muted-foreground">
          Visualize flight routes on Mapbox
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Map</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="text-sm text-muted-foreground">
              Loading flights…
            </div>
          )}
          {error && (
            <div className="text-sm text-red-400">
              Failed to load flights. Make sure the backend is running.
            </div>
          )}
          <Map height="600px" route={route} />
        </CardContent>
      </Card>
    </div>
  );
}
