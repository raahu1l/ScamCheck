import { useState } from "react";

export default function ResultCard({ result }) {
  const [open, setOpen] = useState(null);

  const verdict = result.verdict || "Caution";

  const verdictClass =
    verdict === "High Risk"
      ? "high"
      : verdict === "Caution"
        ? "caution"
        : "safe";

  const contextual = result.contextual || {};
  const structural = result.structural || {};
  const technical = result.technical || {};

  const sections = [
    {
      key: "structural",
      title: "Structural signals",
      flag: structural.flag,
      details:
        structural.matched?.length
          ? structural.matched.map((x) => x.replace(/\\s\+/g, " ")).join(", ")
          : "No suspicious template patterns detected.",
    },
    {
      key: "technical",
      title: "Technical signals",
      flag: technical.flag,
      details:
        technical.url_signal?.matched_fields?.length
          ? technical.url_signal.matched_fields.join(", ")
          : technical.text_signal?.note ||
            "No strong technical red flags detected.",
    },
    {
      key: "contextual",
      title: "Contextual reasoning",
      flag: contextual.contextual_flag,
      details:
        contextual.flags_triggered?.length
          ? contextual.flags_triggered.join(" • ")
          : "No significant contextual red flags detected.",
    },
  ];

  return (
    <section className="result-card">
      <div className={`verdict ${verdictClass}`}>
        <div className="verdict-icon">
          {verdict === "High Risk" ? "!" : verdict === "Caution" ? "?" : "✓"}
        </div>
        <div>
          <div className="verdict-label">SCAMCHECK VERDICT</div>
          <h2>{verdict}</h2>
        </div>
      </div>

      <p className="result-intro">
        The verdict combines independent structural, technical and contextual
        signals.
      </p>

      <div className="signal-list">
        {sections.map((section) => (
          <div className="signal" key={section.key}>
            <button
              className="signal-header"
              onClick={() =>
                setOpen(open === section.key ? null : section.key)
              }
            >
              <span>
                <b className={section.flag ? "flag-dot" : "safe-dot"} />
                {section.title}
              </span>
              <span>{open === section.key ? "−" : "+"}</span>
            </button>

            {open === section.key && (
              <div className="signal-details">{section.details}</div>
            )}
          </div>
        ))}
      </div>

      {contextual.follow_up_question && (
        <div className="question-box">
          <div className="box-label">VERIFY THIS</div>
          <p>{contextual.follow_up_question}</p>
        </div>
      )}

      {contextual.advice && (
        <div className="advice-box">
          <div className="box-label">WHAT TO DO</div>
          <p>{contextual.advice}</p>
        </div>
      )}
    </section>
  );
}