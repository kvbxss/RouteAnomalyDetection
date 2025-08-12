import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Flights from "./pages/Flights.tsx";
import Anomalies from "./pages/Anomalies.tsx";
import Chatbot from "./pages/Chatbot.tsx";
import MapView from "./pages/MapView";

// Create a client
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/flights" element={<Flights />} />
            <Route path="/anomalies" element={<Anomalies />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/chatbot" element={<Chatbot />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
