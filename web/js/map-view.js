const TRAIL_SOURCE_ID = "boat-trail";
const TRAIL_LAYER_ID = "boat-trail-line";

// CARTO's free dark-matter style — no API key needed, matches the
// Lattice-style dark map look.
const MAP_STYLE_URL = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

export function initMap(containerId, center) {
    const map = new maplibregl.Map({
        container: containerId,
        style: MAP_STYLE_URL,
        center: [center.lon, center.lat],
        zoom: 15,
    });

    const marker = new maplibregl.Marker({ color: "#3fb1ce" }).setLngLat([center.lon, center.lat]);

    const mapState = { map, marker, trailCoordinates: [] };

    map.on("load", () => {
        marker.addTo(map);
        map.addSource(TRAIL_SOURCE_ID, {
            type: "geojson",
            data: { type: "Feature", geometry: { type: "LineString", coordinates: [] } },
        });
        map.addLayer({
            id: TRAIL_LAYER_ID,
            type: "line",
            source: TRAIL_SOURCE_ID,
            paint: { "line-color": "#3fb1ce", "line-width": 2 },
        });
    });

    return mapState;
}

export function updateBoatPosition(mapState, lat, lon) {
    mapState.marker.setLngLat([lon, lat]);
    mapState.trailCoordinates.push([lon, lat]);

    const source = mapState.map.getSource(TRAIL_SOURCE_ID);
    if (source) {
        source.setData({
            type: "Feature",
            geometry: { type: "LineString", coordinates: mapState.trailCoordinates },
        });
    }
    mapState.map.panTo([lon, lat]);
}

export function setStaleStyle(mapState, isStale) {
    mapState.marker.getElement().style.opacity = isStale ? "0.4" : "1";
}

// A new boat session (reboot) starts a fresh run — connecting its first
// point back to wherever the trail left off would draw a path the boat
// never took.
export function resetTrail(mapState) {
    mapState.trailCoordinates = [];
    const source = mapState.map.getSource(TRAIL_SOURCE_ID);
    if (source) {
        source.setData({
            type: "Feature",
            geometry: { type: "LineString", coordinates: [] },
        });
    }
}
