import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./routes/Home";
import Play from "./routes/Play";
import Profile from "./routes/Profile";
import Operator from "./routes/Operator";
import Library from "./routes/Library";
import LibrarySection from "./routes/LibrarySection";
import LibraryEntry from "./routes/LibraryEntry";
import Configurator from "./routes/Configurator";
import Triage from "./routes/Triage";
import Admin from "./routes/Admin";
import Debug from "./routes/Debug";
import Research from "./routes/Research";
import ResearchHypothesis from "./routes/ResearchHypothesis";
import PlaytestFullCycle from "./routes/PlaytestFullCycle";
import PlaytestFollowup from "./routes/PlaytestFollowup";
import { LangProvider } from "./i18n";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <LangProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/play/:gameId" element={<Play />} />
        <Route path="/session/:sessionId/profile" element={<Profile />} />
        <Route path="/operator" element={<Operator />} />
        <Route path="/library" element={<Library />} />
        <Route path="/library/section/:kind" element={<LibrarySection />} />
        <Route path="/library/entry/:id" element={<LibraryEntry />} />
        <Route path="/configurator" element={<Configurator />} />
        <Route path="/triage" element={<Triage />} />
        <Route path="/admin/materials" element={<Admin />} />
        <Route path="/debug/session/:sessionId" element={<Debug />} />
        <Route path="/research" element={<Research />} />
        <Route path="/research/hypotheses/:id" element={<ResearchHypothesis />} />
        <Route path="/playtest/full-cycle" element={<PlaytestFullCycle />} />
        <Route path="/playtest/followup/:token" element={<PlaytestFollowup />} />
      </Routes>
    </BrowserRouter>
    </LangProvider>
  </React.StrictMode>,
);
