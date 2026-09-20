import { useState } from "react";
import "./App.css";
import SkillInput from "./components/SkillInput";
import ResultCard from "./components/ResultCard";

const API_URL = "http://localhost:5000/analyze";

const WELLBRIDGE_SAMPLE = `Welcome Letter

Congratulations! You have been selected for the internship program.

Batch Code: WT-2026
To confirm your enrolment, complete the required process.
Flexible joining date available.
Selected candidates can refer a friend for additional benefits.`;

const MEDINEX_SAMPLE = `MediNex is looking for a Software Engineering Intern to join our product engineering team. The intern will work with experienced engineers on internal tools and customer-facing web applications.

Responsibilities include implementing frontend components, writing and testing REST API endpoints, fixing bugs, participating in code reviews, and documenting technical changes.

Candidates should have familiarity with JavaScript or TypeScript, basic knowledge of React, Git, and REST APIs, and a willingness to learn.

The internship includes a structured onboarding process and regular mentorship from the engineering team. Candidates will be shortlisted based on their application and may be invited to a technical discussion before selection.

The internship is remote and will run for 8 weeks. Interested candidates can apply through the official company application process. There is no application fee or payment required to apply.`;

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyze = async (content, url) => {
    if (!content.trim() && !url.trim()) {
      setError("Paste the posting text or provide an application link.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          type: "text",
          content: content.trim(),
          url: url.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.error || "Analysis failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message.includes("Failed to fetch")
          ? "Could not connect to ScamCheck backend. Make sure Flask is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="navbar">
        <div className="brand">
          <span className="brand-mark">✓</span>
          ScamCheck
        </div>
        <span className="tagline">Verify before you trust.</span>
      </header>

      <main className="page">
        <section className="hero">
          <div className="eyebrow">AI-ASSISTED SCAM DETECTION</div>
          <h1>Is this opportunity <span>really legitimate?</span></h1>
          <p>
            Analyze internships, jobs and scholarship opportunities using
            multiple independent signals instead of relying on a single AI
            guess.
          </p>
        </section>

        <SkillInput
          onAnalyze={analyze}
          loading={loading}
          onDemo={(text) => analyze(text, "")}
          onClear={() => {
            setResult(null);
            setError("");
          }}
        />

        {error && <div className="error-box">{error}</div>}

        {result && <ResultCard result={result} />}
      </main>

      <footer>
        ScamCheck · Built for HACKDAY 1.0 · Tech for a Better Tomorrow
      </footer>
    </div>
  );
}

export default App;