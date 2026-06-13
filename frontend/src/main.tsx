import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./routes/Home";
import Play from "./routes/Play";
import Profile from "./routes/Profile";
import Operator from "./routes/Operator";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/play/:gameId" element={<Play />} />
        <Route path="/session/:sessionId/profile" element={<Profile />} />
        <Route path="/operator" element={<Operator />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
