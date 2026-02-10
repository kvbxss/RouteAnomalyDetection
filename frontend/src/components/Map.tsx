import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

// Expect token in Vite env
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

export type RoutePoint = [number, number]; // [lng, lat]

export interface AnomalyMarker {
  id: number;
  position: [number, number]; // [lng, lat]
  type: string;
  confidence: number;
  flightId: string;
}
export interface LiveFlightMarker {
  icao24: string;            // Mode S hex
  callsign: string;
  position: [number, number]; // [lng, lat]
  altitude: number;
  speed: number;
  heading: number;
}

export interface LiveFlightTrack {
  icao24: string;
  coordinates: [number, number][];
}
 

interface MapProps {
  center?: [number, number];
  zoom?: number;
  height?: string;
  liveFlights?: LiveFlightMarker[]; // live flight markers
  liveTracks?: LiveFlightTrack[]; // live flight trails
  route?: RoutePoint[]; // optional route as [lng,lat]
  anomalyMarkers?: AnomalyMarker[]; // anomaly markers
  onMarkerClick?: (anomaly: AnomalyMarker) => void; // callback when marker clicked
}

export default function Map({
  center = [0, 20],
  zoom = 1.5,
  height = "500px",
  route,
  anomalyMarkers = [],
  onMarkerClick,
  liveFlights = [],
  liveTracks = [],
}: MapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const routeMarkersRef = useRef<mapboxgl.Marker[]>([]);
  const liveFlightMarkersRef = useRef<mapboxgl.Marker[]>([]);
  const mapLoadedRef = useRef(false);
  
  // Show helpful message if token is missing
  if (!MAPBOX_TOKEN) {
    return (
      <div className="relative">
        <div
          className="flex items-center justify-center bg-muted/20 rounded-lg border-2 border-dashed border-muted"
          style={{ width: "100%", height }}
        >
          <div className="flex flex-col items-center gap-3 text-center max-w-md p-6">
            <svg
              className="h-12 w-12 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-foreground mb-2">Mapbox Token Required</p>
              <p className="text-xs text-muted-foreground mb-3">
                Configure your Mapbox access token to display the interactive map.
              </p>
              <ol className="text-xs text-muted-foreground text-left space-y-1.5 mb-3 bg-muted/50 p-3 rounded">
                <li>1. Get a free token at <a href="https://account.mapbox.com/access-tokens/" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline font-medium">mapbox.com</a></li>
                <li>2. Create <code className="bg-background px-1.5 py-0.5 rounded text-xs font-mono">frontend/.env.local</code></li>
                <li>3. Add: <code className="bg-background px-1.5 py-0.5 rounded text-xs font-mono">VITE_MAPBOX_TOKEN=your_token</code></li>
                <li>4. Restart the dev server</li>
              </ol>
              <p className="text-xs text-muted-foreground italic">See frontend/.env.example for reference</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Get color based on anomaly type
  const getMarkerColor = (type: string): string => {
    const colors: Record<string, string> = {
      'altitude_anomaly': '#dc2626', // red
      'speed_anomaly': '#ea580c', // orange
      'route_deviation': '#eab308', // yellow
      'temporal_anomaly': '#2563eb', // blue
      'combined': '#9333ea', // purple
    };
    return colors[type] || '#6b7280'; // gray default
  };

  const updateRoute = (map: mapboxgl.Map) => {
    if (!route || route.length < 2) {
      if (map.getLayer("route-line")) {
        map.removeLayer("route-line");
      }
      if (map.getSource("route")) {
        map.removeSource("route");
      }
      routeMarkersRef.current.forEach(marker => marker.remove());
      routeMarkersRef.current = [];
      return;
    }

    const geojson = {
      type: "Feature",
      geometry: { type: "LineString", coordinates: route },
      properties: {},
    };

    const source = map.getSource("route") as mapboxgl.GeoJSONSource | undefined;
    if (source) {
      source.setData(geojson);
    } else {
      map.addSource("route", { type: "geojson", data: geojson });
      map.addLayer({
        id: "route-line",
        type: "line",
        source: "route",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#2563eb", "line-width": 4 },
      });
    }

    routeMarkersRef.current.forEach(marker => marker.remove());
    routeMarkersRef.current = [];

    routeMarkersRef.current.push(
      new mapboxgl.Marker({ color: "#10b981" })
        .setLngLat(route[0])
        .setPopup(new mapboxgl.Popup().setHTML("<strong>Start</strong>"))
        .addTo(map)
    );

    routeMarkersRef.current.push(
      new mapboxgl.Marker({ color: "#ef4444" })
        .setLngLat(route[route.length - 1])
        .setPopup(new mapboxgl.Popup().setHTML("<strong>End</strong>"))
        .addTo(map)
    );

    const bounds = route.reduce(
      (b, [lng, lat]) => b.extend([lng, lat]),
      new mapboxgl.LngLatBounds(route[0], route[0])
    );
    map.fitBounds(bounds, { padding: 40, duration: 800 });
  };

  const updateAnomalies = (map: mapboxgl.Map) => {
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    if (anomalyMarkers.length === 0) return;

    anomalyMarkers.forEach(anomaly => {
      const el = document.createElement("div");
      el.className = "anomaly-marker";
      el.style.backgroundColor = getMarkerColor(anomaly.type);
      el.style.width = "20px";
      el.style.height = "20px";
      el.style.borderRadius = "50%";
      el.style.border = "2px solid white";
      el.style.boxShadow = "0 2px 4px rgba(0,0,0,0.3)";
      el.style.cursor = "pointer";
      el.style.transition = "transform 0.2s";

      el.addEventListener("mouseenter", () => (el.style.transform = "scale(1.2)"));
      el.addEventListener("mouseleave", () => (el.style.transform = "scale(1)"));

      const popupContent = `
        <div style="padding: 4px;">
          <strong>${anomaly.flightId}</strong><br/>
          <span style="color: ${getMarkerColor(anomaly.type)}">
            ${anomaly.type}
          </span><br/>
          <small>Confidence: ${(anomaly.confidence * 100).toFixed(1)}%</small>
        </div>
      `;

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat(anomaly.position)
        .setPopup(new mapboxgl.Popup({ offset: 25 }).setHTML(popupContent))
        .addTo(map);

      if (onMarkerClick) el.addEventListener("click", () => onMarkerClick(anomaly));

      markersRef.current.push(marker);
    });

    if (!route || route.length === 0) {
      const bounds = new mapboxgl.LngLatBounds();
      anomalyMarkers.forEach(a => bounds.extend(a.position));
      map.fitBounds(bounds, { padding: 60, duration: 800 });
    }
  };

  const updateLiveFlights = (map: mapboxgl.Map) => {
    liveFlightMarkersRef.current.forEach(marker => marker.remove());
    liveFlightMarkersRef.current = [];

    if (!liveFlights || liveFlights.length === 0) return;

    liveFlights.forEach(flight => {
      const el = document.createElement("div");
      el.className = "live-flight-marker";
      el.style.width = "18px";
      el.style.height = "18px";
      el.style.backgroundColor = "#3b82f6"; // blue
      el.style.borderRadius = "50%";
      el.style.border = "2px solid white";
      el.style.boxShadow = "0 1px 3px rgba(0,0,0,0.3)";
      el.style.transform = `rotate(${flight.heading}deg)`;

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat(flight.position)
        .setPopup(
          new mapboxgl.Popup({ offset: 25 }).setHTML(`
            <strong>${flight.callsign}</strong><br/>
            Alt: ${flight.altitude} ft<br/>
            Speed: ${flight.speed} kt<br/>
            Hex: ${flight.icao24}
          `)
        )
        .addTo(map);

      liveFlightMarkersRef.current.push(marker);
    });
  };

  const updateLiveTracks = (map: mapboxgl.Map) => {
    if (!liveTracks || liveTracks.length === 0) {
      if (map.getLayer("live-tracks-line")) {
        map.removeLayer("live-tracks-line");
      }
      if (map.getSource("live-tracks")) {
        map.removeSource("live-tracks");
      }
      return;
    }

    const featureCollection = {
      type: "FeatureCollection",
      features: liveTracks
        .filter(t => t.coordinates.length >= 2)
        .map(t => ({
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates: t.coordinates,
          },
          properties: { icao24: t.icao24 },
        })),
    };

    const source = map.getSource("live-tracks") as mapboxgl.GeoJSONSource | undefined;
    if (source) {
      source.setData(featureCollection as any);
    } else {
      map.addSource("live-tracks", {
        type: "geojson",
        data: featureCollection as any,
      });
      map.addLayer({
        id: "live-tracks-line",
        type: "line",
        source: "live-tracks",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#60a5fa", "line-width": 2, "line-opacity": 0.7 },
      });
    }
  };

  useEffect(() => {
    if (!containerRef.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center,
      zoom,
    });

    map.addControl(
      new mapboxgl.NavigationControl({ visualizePitch: true }),
      "top-right"
    );
    mapRef.current = map;

    map.on("load", () => {
      mapLoadedRef.current = true;
      updateRoute(map);
      updateAnomalies(map);
      updateLiveFlights(map);
      updateLiveTracks(map);
    });

    return () => {
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current = [];
      routeMarkersRef.current.forEach(marker => marker.remove());
      routeMarkersRef.current = [];
      liveFlightMarkersRef.current.forEach(marker => marker.remove());
      liveFlightMarkersRef.current = [];
      map.remove();
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.jumpTo({ center, zoom });
  }, [center[0], center[1], zoom]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoadedRef.current) return;
    updateRoute(map);
    updateAnomalies(map);
    updateLiveFlights(map);
    updateLiveTracks(map);
  }, [route, anomalyMarkers, liveFlights, liveTracks, onMarkerClick]);
  
  return (
    <div className="relative">
      <div ref={containerRef} style={{ width: "100%", height }} />

      {/* Legend */}
      {anomalyMarkers.length > 0 && (
        <div className="absolute bottom-4 right-4 bg-white/95 dark:bg-gray-900/95 rounded-lg shadow-lg p-3 text-xs">
          <div className="font-semibold mb-2">Anomaly Types</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#dc2626' }}></div>
              <span>Altitude</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ea580c' }}></div>
              <span>Speed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#eab308' }}></div>
              <span>Route</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#2563eb' }}></div>
              <span>Temporal</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#9333ea' }}></div>
              <span>Combined</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
