import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";

// Expect token in Vite env
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

export type RoutePoint = [number, number]; // [lng, lat]

interface MapProps {
  center?: [number, number];
  zoom?: number;
  height?: string;
  route?: RoutePoint[]; // optional route as [lng,lat]
}

export default function Map({
  center = [0, 20],
  zoom = 1.5,
  height = "500px",
  route,
}: MapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    if (!MAPBOX_TOKEN) {
      console.warn("VITE_MAPBOX_TOKEN not set. Map will not load.");
      return;
    }

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
      if (route && route.length >= 2) {
        map.addSource("route", {
          type: "geojson",
          data: {
            type: "Feature",
            geometry: {
              type: "LineString",
              coordinates: route,
            },
            properties: {},
          },
        });
        map.addLayer({
          id: "route-line",
          type: "line",
          source: "route",
          layout: { "line-join": "round", "line-cap": "round" },
          paint: { "line-color": "#2563eb", "line-width": 4 },
        });
        // Fit bounds
        const bounds = route.reduce(
          (b, [lng, lat]) => b.extend([lng, lat]),
          new mapboxgl.LngLatBounds(route[0], route[0])
        );
        map.fitBounds(bounds, { padding: 40, duration: 800 });
      }
    });

    return () => {
      map.remove();
    };
  }, [center[0], center[1], zoom, route]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
}
