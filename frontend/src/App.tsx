import "./App.css";
import {useState} from "react";
import UploadForm from "./components/UploadForm";
import ReportsList from "./components/ReportsList";

function App() {
  console.log("App component loaded!");

  const [reloadKey, setReloadKey] = useState(0);

  const handleUploadSuccess = () => {
    setReloadKey((prev) => prev + 1); // Trigger a remount of ReportsList
  };

  return (
    <div className="App">
      <header style={{padding: "1rem", borderBottom: "1px solid #ccc"}}>
        <h1>📊 Trivy UI</h1>
        <p style={{color: "#555"}}>
          Explore security reports with filtering and summary views
        </p>
      </header>

      <main style={{padding: "1rem"}}>
        <UploadForm onUploadSuccess={handleUploadSuccess} />
        <ReportsList key={reloadKey} />
      </main>
    </div>
  );
}

export default App;
