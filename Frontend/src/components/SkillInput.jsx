import { useState } from "react";

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

export default function SkillInput({ onAnalyze, loading, onDemo, onClear }) {
  const [content, setContent] = useState("");
  const [url, setUrl] = useState("");

  const submit = () => {
    onAnalyze(content, url);
  };

  const loadDemo = (text) => {
    setContent(text);
    setUrl("");
    onDemo(text);
  };

  return (
    <section className="input-card">
      <div className="section-label">CHECK AN OPPORTUNITY</div>

      <label>Job / Internship / Scholarship Content</label>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Paste the complete opportunity message here..."
        rows={9}
        disabled={loading}
      />

      <label>
        Application / Posting Link <span>(optional)</span>
      </label>
      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com/apply"
        disabled={loading}
      />

      <button className="analyze-btn" onClick={submit} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze Opportunity →"}
      </button>

      <div className="demo-divider">
        <span>OR TRY A REAL SAMPLE</span>
      </div>

      <div className="demo-buttons">
        <button
          onClick={() => loadDemo(WELLBRIDGE_SAMPLE)}
          disabled={loading}
        >
          🚩 Reported Scam
        </button>

        <button
          onClick={() => loadDemo(MEDINEX_SAMPLE)}
          disabled={loading}
        >
          ✓ Legitimate Posting
        </button>
      </div>

      {(content || url) && !loading && (
        <button className="clear-btn" onClick={onClear}>
          Clear
        </button>
      )}
    </section>
  );
}