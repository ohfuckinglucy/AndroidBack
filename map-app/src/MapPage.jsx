import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, TimeScale, PointElement, LineElement, Title, Tooltip, Legend);

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png").default,
  iconUrl: require("leaflet/dist/images/marker-icon.png").default,
  shadowUrl: require("leaflet/dist/images/marker-shadow.png").default,
});

const baseStationIcon = new L.Icon({
  iconUrl: "/icons/base_station.png",
  iconSize: [32, 32],
  iconAnchor: [16, 32],
});

const handoverIcon = L.divIcon({
  html: `<div style="background:red;border-radius:50%;width:16px;height:16px"></div>`,
  iconSize: [16, 16],
});

function getSignalColor(rsrp) {
  if (rsrp == null) return "gray";
  if (rsrp >= -80) return "green";
  if (rsrp >= -90) return "lime";
  if (rsrp >= -100) return "yellow";
  if (rsrp >= -110) return "orange";
  return "red";
}

function filterPointsByDistance(points, minDistance = 0.00005) {
  if (!points.length) return [];
  const filtered = [points[0]];
  for (let i = 1; i < points.length; i++) {
    const last = filtered[filtered.length - 1];
    const p = points[i];
    const dLat = p.lat - last.lat;
    const dLng = p.lng - last.lng;
    if (Math.sqrt(dLat * dLat + dLng * dLng) >= minDistance) filtered.push(p);
  }
  return filtered;
}

const MapPage = () => {
  const [positions, setPositions] = useState([]);
  const [baseStations, setBaseStations] = useState([]);
  const [handovers, setHandovers] = useState([]);
  const [activeTab, setActiveTab] = useState("map");
  const [showBaseStations, setShowBaseStations] = useState(false);
  const [showHandovers, setShowHandovers] = useState(false);

  useEffect(() => {
    fetch("http://localhost:5000/api/route")
      .then((res) => res.json())
      .then((data) => {
        setPositions(filterPointsByDistance(
          data.route.map((p) => ({ lat: +p.latitude, lng: +p.longitude, rsrp: p.rsrp, timestamp: p.timestamp }))
        ));

        setBaseStations(data.base_stations.map((bs) => ({
          lat: +bs.latitude,
          lng: +bs.longitude,
          pci: bs.pci,
          earfcn: bs.earfcn,
          pointCount: bs.point_count,
          avgRsrp: bs.avg_rsrp,
        })));

        setHandovers(data.handovers || []);
      })
      .catch((err) => console.error(err));
  }, []);

  if (!positions.length) return <div>Нет данных.</div>;

  const mapCenter = [positions[0].lat, positions[0].lng];

  const validPositions = positions.filter((p) => p.rsrp != null);
  const lineData = {
    labels: validPositions.map((p) => new Date(p.timestamp * 1000).toLocaleTimeString()),
    datasets: [{
      label: "RSRP (dBm)",
      data: validPositions.map((p) => p.rsrp),
      borderColor: "rgb(75,192,192)",
      backgroundColor: "rgba(75,192,192,0.2)",
      tension: 0.2,
    }],
  };
  const lineOptions = {
    responsive: true,
    plugins: { legend: { position: "top" }, title: { display: true, text: "RSRP во времени" } },
    scales: { y: { min: -140, max: -40, reverse: true } },
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ width: "200px", padding: "10px", borderRight: "1px solid #ddd" }}>
        <button onClick={() => setShowBaseStations(!showBaseStations)}>
          {showBaseStations ? "Скрыть БС" : "Показать БС"}
        </button>
        <br />
        <button onClick={() => setShowHandovers(!showHandovers)}>
          {showHandovers ? "Скрыть хендоверы" : "Показать хендоверы"}
        </button>
        <hr />
        <div style={{ fontSize: "12px" }}>Версия 1.0 — 09.12.2025</div>
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "10px", borderBottom: "1px solid #ddd" }}>
          <button onClick={() => setActiveTab("map")}>Карта</button>
          <button onClick={() => setActiveTab("graphs")}>Графики</button>
        </div>

        <div style={{ flex: 1 }}>
          {activeTab === "map" && (
            <MapContainer center={mapCenter} zoom={13} style={{ height: "100%", width: "100%" }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

              {showBaseStations && baseStations.map((bs, i) => (
                <Marker key={i} position={[bs.lat, bs.lng]} icon={baseStationIcon}>
                  <Popup>
                    PCI: {bs.pci}, EARFCN: {bs.earfcn} <br />
                    Точек: {bs.pointCount} <br />
                    Средний RSRP: {bs.avgRsrp?.toFixed(1) ?? "—"} dBm
                  </Popup>
                </Marker>
              ))}

              {showHandovers && handovers.map((ho, i) => (
                <Marker key={i} position={[+ho.position.latitude, +ho.position.longitude]} icon={handoverIcon}>
                  <Popup>
                    От: PCI {ho.from.pci}, EARFCN {ho.from.earfcn} <br />
                    К: PCI {ho.to.pci}, EARFCN {ho.to.earfcn}
                  </Popup>
                </Marker>
              ))}

              {positions.slice(0, -1).map((p, i) => (
                <Polyline
                  key={i}
                  positions={[[p.lat, p.lng], [positions[i + 1].lat, positions[i + 1].lng]]}
                  pathOptions={{ color: getSignalColor(p.rsrp), weight: 5 }}
                />
              ))}
            </MapContainer>
          )}

          {activeTab === "graphs" && (
            <div style={{ padding: "20px" }}>
              <h3>RSRP во времени</h3>
              <Line data={lineData} options={lineOptions} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MapPage;
