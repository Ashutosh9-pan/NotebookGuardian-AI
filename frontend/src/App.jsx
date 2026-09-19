import { useEffect, useMemo, useRef, useState } from "react";
import { jsPDF } from "jspdf";
import {
  Activity,
  AlertTriangle,
  Check,
  Copy,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Code2,
  Download,
  File,
  FileCode2,
  Github,
  Info,
  LoaderCircle,
  LockKeyhole,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  XCircle,
  X
} from "lucide-react";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000/analyze";


/* =========================================================
   HELPERS
========================================================= */

function riskClass(level) {
  return String(level || "LOW").toLowerCase();
}


function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return "—";

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}


function pct(value) {
  return Number(value || 0);
}


/* =========================================================
   RISK HELPERS
========================================================= */

function getRisk(cell, type) {
  const direct = cell?.[`${type}_risk_percentage`];

  const obj = cell?.[`${type}_risk`];

  const probability = cell?.[`${type}_risk_probability`];

  return {
    percentage: pct(
      direct ??
        obj?.risk_percentage ??
        (probability != null ? Number(probability) * 100 : 0)
    ),

    level:
      cell?.[`${type}_risk_level`] ||
      obj?.risk_level ||
      "LOW"
  };
}


function isDualCell(cell) {
  return Boolean(
    cell?.code_risk_percentage != null ||
      cell?.execution_risk_percentage != null ||
      cell?.code_risk ||
      cell?.execution_risk
  );
}


/*
  IMPORTANT:

  In dual-risk mode, a cell gets ONE combined risk level.

  We use the higher of:
    - Code Risk
    - Execution Risk

  This keeps:
    HIGH + LOW       => HIGH
    MEDIUM + LOW     => MEDIUM
    LOW + LOW        => LOW
    HIGH + MEDIUM    => HIGH
    MEDIUM + HIGH    => HIGH

  The same logic is used by:
    - filters
    - risk distribution
    - cell border
    - modal
*/
function getCombinedRisk(cell, dual = true) {
  if (!dual) {
    return {
      percentage: pct(cell?.risk_percentage),
      level: cell?.risk_level || "LOW"
    };
  }

  const codeRisk = getRisk(cell, "code");
  const executionRisk = getRisk(cell, "execution");

  if (codeRisk.percentage >= executionRisk.percentage) {
    return {
      percentage: codeRisk.percentage,
      level: codeRisk.level || "LOW"
    };
  }

  return {
    percentage: executionRisk.percentage,
    level: executionRisk.level || "LOW"
  };
}


/* =========================================================
   COMPONENTS
========================================================= */

function RiskBadge({ level }) {
  return (
    <span className={`risk-badge ${riskClass(level)}`}>
      {level || "LOW"}
    </span>
  );
}


function SummaryCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = "neutral"
}) {
  return (
    <article className={`summary-card ${tone}`}>
      <div className="summary-icon">
        <Icon size={20} />
      </div>

      <div>
        <p className="summary-label">{label}</p>

        <h3>{value}</h3>

        <p className="summary-hint">{hint}</p>
      </div>
    </article>
  );
}


function RiskMetric({ label, risk, tone }) {
  return (
    <div className={`dual-metric ${tone}`}>
      <div className="dual-metric-head">
        <span>{label}</span>

        <RiskBadge level={risk.level} />
      </div>

      <div className="dual-percent">
        {risk.percentage.toFixed(2)}%
      </div>

      <div className="dual-meter">
        <span
          style={{
            width: `${Math.min(risk.percentage, 100)}%`
          }}
        />
      </div>
    </div>
  );
}


/* =========================================================
   CELL CARD
========================================================= */

function getRiskExplanation(cell, dual) {
  const codeRisk = getRisk(cell, "code");
  const executionRisk = getRisk(cell, "execution");
  const reasons = cell?.reasons || [];

  if (!dual) {
    return {
      title: "Why this cell was flagged",
      summary:
        reasons.length > 0
          ? "The model detected one or more signals associated with higher notebook risk."
          : "The model assigned this cell a higher risk probability based on its learned feature patterns.",
      drivers: reasons.length
        ? reasons
        : ["Model probability is above the configured risk threshold."],
      action:
        "Review the cell logic, inputs, and dependencies before relying on its output."
    };
  }

  const dominant =
    executionRisk.percentage > codeRisk.percentage
      ? "execution"
      : codeRisk.percentage > executionRisk.percentage
        ? "code"
        : "both";

  let summary;

  if (dominant === "execution") {
    summary =
      "Execution-state signals contribute more to this cell's combined risk than code-structure signals.";
  } else if (dominant === "code") {
    summary =
      "Code-structure signals contribute more to this cell's combined risk than execution-state signals.";
  } else {
    summary =
      "Code-structure and execution-state signals contribute similarly to this cell's combined risk.";
  }

  const drivers = reasons.length
    ? reasons
    : ["No specific textual signal was returned by the analyzer."];

  let action =
    "Review the cell before relying on its output, especially its dependencies and inputs.";

  if (executionRisk.percentage >= codeRisk.percentage && executionRisk.percentage >= 60) {
    action =
      "Check execution count, execution order, and whether required upstream cells were run after changes.";
  } else if (codeRisk.percentage > executionRisk.percentage && codeRisk.percentage >= 70) {
    action =
      "Review the cell's code structure, data operations, model operations, and external resource usage.";
  }

  return {
    title: "Why this cell was flagged",
    summary,
    drivers,
    action
  };
}


function CellCard({ cell, dual, onPreview }) {
  const [open, setOpen] = useState(false);
  const [showWhy, setShowWhy] = useState(false);

  const codeRisk = getRisk(cell, "code");

  const executionRisk = getRisk(cell, "execution");

  const combinedRisk = getCombinedRisk(cell, dual);

  const singleLevel = cell?.risk_level || "LOW";

  const singlePct = pct(cell?.risk_percentage);

  const combinedLevel = dual
    ? combinedRisk.level
    : singleLevel;

  const explanation = getRiskExplanation(cell, dual);


  return (
    <article
      className={`cell-card ${riskClass(combinedLevel)}`}
    >
      {/* CELL HEADER */}
      <div className="cell-card-top">

        <div className="cell-title-wrap">

          <div className="cell-number">
            #{cell.cell_number}
          </div>

          <div>

            <div className="cell-heading-row">

              <h4>
                Code Cell {cell.cell_number}
              </h4>

              {dual ? (
                <span className="dual-chip">
                  <BrainCircuit size={12} />
                  Dual risk
                </span>
              ) : (
                <RiskBadge level={singleLevel} />
              )}

            </div>

            <p className="cell-subtitle">
              Execution count:{" "}
              {cell.execution_count ?? "Not executed"}
            </p>

          </div>
        </div>


        {!dual && (
          <div className="cell-risk-block">

            <strong>
              {singlePct.toFixed(2)}%
            </strong>

            <span>
              risk probability
            </span>

          </div>
        )}

      </div>


      {/* RISK METRICS */}
      {dual ? (
        <div className="dual-risk-grid">

          <RiskMetric
            label="Code Risk"
            risk={codeRisk}
            tone="code"
          />

          <RiskMetric
            label="Execution Risk"
            risk={executionRisk}
            tone="execution"
          />

        </div>
      ) : (
        <div className="risk-meter">

          <span
            className={`risk-meter-fill ${riskClass(
              singleLevel
            )}`}
            style={{
              width: `${Math.min(singlePct, 100)}%`
            }}
          />

        </div>
      )}


      {/* REASONS */}
      <div className="reason-list">

        {(cell.reasons || []).length > 0 ? (
          cell.reasons.map((reason, index) => (
            <div
              className="reason-item"
              key={`${cell.cell_number}-${index}`}
            >
              <AlertTriangle size={15} />

              <span>{reason}</span>
            </div>
          ))
        ) : (
          <div className="reason-item">
            <AlertTriangle size={15} />

            <span>
              No strong risk pattern detected
            </span>
          </div>
        )}

      </div>


      {/* WHY FLAGGED */}
      <div
        className="why-flagged-visible-wrap"
        style={{
          display: "block",
          width: "100%",
          marginTop: "10px",
          marginBottom: "2px"
        }}
      >
        <button
          className={`why-flagged-visible-button ${showWhy ? "active" : ""}`}
          type="button"
          onClick={() => setShowWhy((value) => !value)}
          aria-expanded={showWhy}
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "7px",
            minHeight: "34px",
            padding: "8px 12px",
            border: "1px solid #d9d4ff",
            borderRadius: "9px",
            background: showWhy ? "#f1efff" : "#ffffff",
            color: "#5b3df5",
            fontSize: "12px",
            fontWeight: 700,
            lineHeight: 1,
            cursor: "pointer",
            boxShadow: showWhy ? "0 4px 12px rgba(91, 61, 245, 0.10)" : "none"
          }}
        >
          <Info size={15} />
          {showWhy ? "Hide explanation" : "Why is this flagged?"}
          {showWhy ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {showWhy && (
          <div
            className="risk-explanation-visible"
            style={{
              width: "100%",
              boxSizing: "border-box",
              marginTop: "9px",
              padding: "14px 15px",
              border: "1px solid #e2defc",
              borderRadius: "12px",
              background: "linear-gradient(135deg, #faf9ff 0%, #f7f9ff 100%)",
              color: "#334155"
            }}
          >
            <div
              className="risk-explanation-visible-head"
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "10px"
              }}
            >
              <div
                style={{
                  flex: "0 0 30px",
                  width: "30px",
                  height: "30px",
                  display: "grid",
                  placeItems: "center",
                  borderRadius: "9px",
                  background: "#ebe8ff",
                  color: "#5b3df5"
                }}
              >
                <Info size={16} />
              </div>

              <div style={{ minWidth: 0 }}>
                <strong
                  style={{
                    display: "block",
                    fontSize: "13px",
                    color: "#172033",
                    marginBottom: "3px"
                  }}
                >
                  {explanation.title}
                </strong>

                <p
                  style={{
                    margin: 0,
                    fontSize: "12px",
                    lineHeight: 1.55,
                    color: "#64748b"
                  }}
                >
                  {explanation.summary}
                </p>
              </div>
            </div>

            <div
              style={{
                marginTop: "13px",
                paddingTop: "11px",
                borderTop: "1px solid #e7e4f7"
              }}
            >
              <span
                style={{
                  display: "block",
                  marginBottom: "7px",
                  fontSize: "11px",
                  fontWeight: 800,
                  color: "#5b3df5",
                  textTransform: "uppercase",
                  letterSpacing: "0.04em"
                }}
              >
                Detected signals
              </span>

              {explanation.drivers.map((driver, index) => (
                <div
                  key={`${cell.cell_number}-driver-${index}`}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "8px",
                    marginTop: "6px",
                    fontSize: "12px",
                    lineHeight: 1.5,
                    color: "#526174"
                  }}
                >
                  <span
                    style={{
                      flex: "0 0 6px",
                      width: "6px",
                      height: "6px",
                      marginTop: "6px",
                      borderRadius: "50%",
                      background: "#5b3df5"
                    }}
                  />
                  <span>{driver}</span>
                </div>
              ))}
            </div>

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                marginTop: "13px",
                padding: "10px 11px",
                borderRadius: "9px",
                background: "#ffffff",
                border: "1px solid #e5e7eb"
              }}
            >
              <strong
                style={{
                  fontSize: "11px",
                  color: "#172033"
                }}
              >
                Review suggestion
              </strong>

              <span
                style={{
                  fontSize: "12px",
                  lineHeight: 1.5,
                  color: "#64748b"
                }}
              >
                {explanation.action}
              </span>
            </div>
          </div>
        )}
      </div>


      {/* CODE ACTIONS */}
      <div className="code-actions">

        <button
          className="code-toggle"
          onClick={() =>
            setOpen((value) => !value)
          }
        >
          <Code2 size={16} />

          {open
            ? "Hide code preview"
            : "Quick preview"}

          {open ? (
            <ChevronUp size={16} />
          ) : (
            <ChevronDown size={16} />
          )}

        </button>


        <button
          className="modal-preview-button"
          onClick={() =>
            onPreview(cell)
          }
        >
          <Code2 size={15} />

          Open full code
        </button>

      </div>


      {/* QUICK PREVIEW */}
      {open && (
        <pre className="code-preview">
          <code>
            {cell.code_preview ||
              "No preview available."}
          </code>
        </pre>
      )}

    </article>
  );
}


/* =========================================================
   FEATURE CARD
========================================================= */

function FeatureCard({
  icon: Icon,
  title,
  text,
  tone
}) {
  return (
    <article className={`feature-card ${tone}`}>

      <div className="feature-icon">
        <Icon size={23} />
      </div>

      <div>

        <h4>{title}</h4>

        <p>{text}</p>

      </div>

    </article>
  );
}


/* =========================================================
   DUAL SUMMARY
========================================================= */

function dualSummary(result, type) {
  const key = `${type}_risk_summary`;

  if (result?.[key]) {
    return result[key];
  }

  if (result?.summary?.[key]) {
    return result.summary[key];
  }

  const cells =
    result?.all_cells ||
    result?.top_dual_risk_cells ||
    result?.top_risky_cells ||
    [];

  let high = 0;
  let medium = 0;
  let low = 0;

  cells.forEach((cell) => {
    const risk = getRisk(cell, type);

    if (risk.level === "HIGH") {
      high++;
    } else if (risk.level === "MEDIUM") {
      medium++;
    } else {
      low++;
    }
  });

  return {
    high_risk_cells: high,
    medium_risk_cells: medium,
    low_risk_cells: low
  };
}


/* =========================================================
   CODE PREVIEW MODAL
========================================================= */

function CodePreviewModal({
  cell,
  dual,
  onClose
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setCopied(false);
  }, [cell]);

  if (!cell) {
    return null;
  }

  async function handleCopyCode() {
    const code = cell.code_preview || "";
    if (!code) return;

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(code);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = code;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }

      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  const codeRisk = getRisk(cell, "code");

  const executionRisk = getRisk(
    cell,
    "execution"
  );

  const combinedRisk = getCombinedRisk(
    cell,
    dual
  );

  const level = dual
    ? combinedRisk.level
    : cell?.risk_level || "LOW";


  return (
    <div
      className="code-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="code-modal-title"
      onMouseDown={onClose}
    >

      <div
        className="code-modal"
        onMouseDown={(event) =>
          event.stopPropagation()
        }
      >

        {/* HEADER */}
        <div className="code-modal-header">

          <div className="code-modal-title">

            <div className="modal-cell-icon">
              <Code2 size={20} />
            </div>

            <div>

              <span>
                NotebookGuardian
              </span>

              <h3 id="code-modal-title">
                Code Cell #{cell.cell_number}
              </h3>

            </div>

          </div>


          <button
            className="modal-close"
            onClick={onClose}
            aria-label="Close code preview"
          >
            <X size={19} />
          </button>

        </div>


        {/* META */}
        <div className="code-modal-meta">

          <RiskBadge
            level={level || "LOW"}
          />

          {dual && (
            <>
              <span className="modal-risk-stat">
                Code{" "}
                {codeRisk.percentage.toFixed(2)}%
              </span>

              <span className="modal-risk-stat">
                Execution{" "}
                {executionRisk.percentage.toFixed(2)}%
              </span>
            </>
          )}

          <span className="modal-risk-stat">
            Execution count:{" "}
            {cell.execution_count ??
              "Not executed"}
          </span>

        </div>


        {/* EDITOR */}
        <div className="code-editor">

          <div className="editor-topbar">

            <div className="editor-dots">
              <i />
              <i />
              <i />
            </div>

            <span>
              cell_{cell.cell_number}.py
            </span>

            <span className="editor-language">
              Python
            </span>

            <button
              className="editor-copy-button"
              onClick={handleCopyCode}
              type="button"
              aria-label={copied ? "Code copied" : "Copy code"}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? "Copied" : "Copy code"}
            </button>

          </div>


          <div className="editor-code">

            <pre>
              <code>
                {cell.code_preview ||
                  "No code preview available."}
              </code>
            </pre>

          </div>

        </div>


        {/* DETECTED SIGNALS */}
        {(cell.reasons || []).length > 0 && (
          <div className="modal-reasons">

            <div className="modal-reasons-title">

              <AlertTriangle size={16} />

              Detected signals

            </div>


            <div className="modal-reason-list">

              {cell.reasons.map(
                (reason, index) => (
                  <span key={index}>
                    {reason}
                  </span>
                )
              )}

            </div>

          </div>
        )}

      </div>

    </div>
  );
}


/* =========================================================
   MAIN APP
========================================================= */

export default function App() {

  const inputRef = useRef(null);


  /* -------------------------------------------------------
     STATE
  ------------------------------------------------------- */

  const [file, setFile] =
    useState(null);

  const [dragging, setDragging] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [result, setResult] =
    useState(null);

  const [error, setError] =
    useState("");


  /* SEARCH / FILTER / MODAL */

  const [searchQuery, setSearchQuery] =
    useState("");

  const [riskFilter, setRiskFilter] =
    useState("ALL");

  const [previewCell, setPreviewCell] =
    useState(null);

  /* -------------------------------------------------------
     MODAL BEHAVIOR
     ------------------------------------------------------- */

  useEffect(() => {
    if (!previewCell) return;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setPreviewCell(null);
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [previewCell]);


  /* -------------------------------------------------------
     DUAL MODE
  ------------------------------------------------------- */

  const dual = useMemo(
    () =>
      Boolean(
        result?.risk_mode === "dual" ||
          result?.dual_risk ||
          result?.top_dual_risk_cells ||
          result?.top_risky_cells?.some(
            isDualCell
          )
      ),
    [result]
  );


  /* -------------------------------------------------------
     OVERALL RISK
  ------------------------------------------------------- */

  const riskPercent = pct(
    result?.summary?.highest_risk_percentage
  );


  /* -------------------------------------------------------
     DUAL SUMMARIES
  ------------------------------------------------------- */

  const codeSummary =
    dualSummary(result, "code");

  const executionSummary =
    dualSummary(result, "execution");


  /* -------------------------------------------------------
     THRESHOLDS
  ------------------------------------------------------- */

  const codeThreshold = pct(
    result?.thresholds?.code ??
      result?.code_threshold ??
      0.70
  );

  const executionThreshold = pct(
    result?.thresholds?.execution ??
      result?.execution_threshold ??
      0.60
  );


  /* =======================================================
     ALL CELLS
  ======================================================= */

  const allCells = useMemo(() => {

    return (
      result?.all_cells ||
      result?.top_dual_risk_cells ||
      result?.top_risky_cells ||
      []
    );

  }, [result]);


  /* =======================================================
     FILTERED CELLS
     
     IMPORTANT FIX:
     
     High / Medium / Low now use the SAME combined
     risk level used by the risk distribution.
     
     Therefore:
     
     All    = 41
     High   = 2
     Medium = 9
     Low    = 30
     
     based on your current notebook result.
  ======================================================= */

  const filteredCells = useMemo(() => {

    let cells = [...allCells];


    /* -----------------------------------------------------
       SEARCH
    ----------------------------------------------------- */

    const query =
      searchQuery.trim().toLowerCase();


    if (query) {

      cells = cells.filter((cell) => {

        const number = String(
          cell?.cell_number ?? ""
        ).toLowerCase();


        const code = String(
          cell?.code_preview ?? ""
        ).toLowerCase();


        const reasons = (
          cell?.reasons || []
        )
          .join(" ")
          .toLowerCase();


        return (
          number.includes(query) ||
          code.includes(query) ||
          reasons.includes(query)
        );

      });

    }


    /* -----------------------------------------------------
       RISK FILTER
    ----------------------------------------------------- */

    if (riskFilter !== "ALL") {

      cells = cells.filter((cell) => {

        /*
          RISK FLAGGED

          Anything that has a meaningful risk signal:
          HIGH or MEDIUM in either model.
        */

        if (riskFilter === "DUAL") {

          const codeRisk =
            getRisk(cell, "code");

          const executionRisk =
            getRisk(
              cell,
              "execution"
            );


          return (
            codeRisk.level === "HIGH" ||
            codeRisk.level === "MEDIUM" ||
            executionRisk.level === "HIGH" ||
            executionRisk.level === "MEDIUM"
          );
        }


        /*
          HIGH / MEDIUM / LOW

          Use ONE combined level.

          This is the important fix.
        */

        const combinedRisk =
          getCombinedRisk(
            cell,
            dual
          );


        return (
          combinedRisk.level ===
          riskFilter
        );

      });

    }


    return cells;

  }, [
    allCells,
    searchQuery,
    riskFilter,
    dual
  ]);


  /* =======================================================
     RISK DISTRIBUTION
     
     IMPORTANT:
     Distribution uses EXACTLY the same combined risk
     logic as the High / Medium / Low filters.
  ======================================================= */

  const distribution = useMemo(() => {

    const counts = {
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0
    };


    allCells.forEach((cell) => {

      const combinedRisk =
        getCombinedRisk(
          cell,
          dual
        );


      const level =
        combinedRisk.level;


      if (
        counts[level] !== undefined
      ) {
        counts[level]++;
      }

    });


    return counts;

  }, [allCells, dual]);


  const maxDistribution =
    Math.max(
      distribution.HIGH,
      distribution.MEDIUM,
      distribution.LOW,
      1
    );


  /* =======================================================
     FILE VALIDATION
  ======================================================= */

  function validateAndSetFile(
    selectedFile
  ) {

    setError("");

    setResult(null);

    setSearchQuery("");

    setRiskFilter("ALL");

    setPreviewCell(null);


    if (!selectedFile) {
      return;
    }


    if (
      !selectedFile.name
        .toLowerCase()
        .endsWith(".ipynb")
    ) {

      setFile(null);

      setError(
        "Please choose a valid .ipynb Jupyter Notebook file."
      );

      return;
    }


    setFile(selectedFile);
  }


  /* =======================================================
     DRAG & DROP
  ======================================================= */

  function handleDrop(event) {

    event.preventDefault();

    setDragging(false);


    validateAndSetFile(
      event.dataTransfer.files?.[0]
    );
  }


  /* =======================================================
     ANALYZE NOTEBOOK
  ======================================================= */

  async function analyzeNotebook() {

    if (!file) {

      setError(
        "Choose a Jupyter Notebook before starting analysis."
      );

      return;
    }


    setLoading(true);

    setError("");

    setResult(null);


    try {

      // Small demo delay so the loading state is clearly visible.
      await new Promise((resolve) =>
        window.setTimeout(resolve, 2000)
      );

      const formData =
        new FormData();

      formData.append(
        "file",
        file
      );


      const response =
        await fetch(
          API_URL,
          {
            method: "POST",
            body: formData
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data?.detail ||
            "Notebook analysis failed."
        );
      }


      setResult(data);


      setTimeout(() => {

        document
          .getElementById("results")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });

      }, 120);


    } catch (err) {

      setError(
        err?.message ||
          "Could not connect to the NotebookGuardian backend. Make sure FastAPI is running on port 8000."
      );

    } finally {

      setLoading(false);

    }
  }


  /* =======================================================
     RESET
  ======================================================= */

  function resetAll() {

    setFile(null);

    setResult(null);

    setError("");

    setSearchQuery("");

    setRiskFilter("ALL");

    setPreviewCell(null);


    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function startNewAnalysis() {
    resetAll();

    window.setTimeout(() => {
      document
        .getElementById("home")
        ?.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });
    }, 50);
  }


  /* =======================================================
     EXPORT PDF REPORT
     ======================================================= */

  function exportReport() {
    if (!result) return;

    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 16;
    const contentWidth = pageWidth - margin * 2;
    let cursorY = 38;

    const addHeader = () => {
      doc.setFillColor(91, 61, 245);
      doc.rect(0, 0, pageWidth, 28, "F");
      doc.setTextColor(255, 255, 255);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(17);
      doc.text("NotebookGuardian AI", margin, 12);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.text("Jupyter Notebook Risk Analysis Report", margin, 20);
      doc.setTextColor(16, 24, 43);
    };

    const ensureSpace = (needed = 12) => {
      if (cursorY + needed > pageHeight - 14) {
        doc.addPage();
        addHeader();
        cursorY = 38;
      }
    };

    const section = (title) => {
      ensureSpace(12);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(49, 42, 112);
      doc.text(title, margin, cursorY);
      cursorY += 7;
    };

    const line = (value, bold = false) => {
      doc.setFont("helvetica", bold ? "bold" : "normal");
      doc.setFontSize(8.5);
      doc.setTextColor(70, 82, 105);
      const lines = doc.splitTextToSize(String(value), contentWidth);
      ensureSpace(lines.length * 4.5 + 3);
      doc.text(lines, margin, cursorY);
      cursorY += lines.length * 4.5 + 3;
    };

    const metric = (label, value, x, y, width) => {
      doc.setFillColor(248, 249, 253);
      doc.setDrawColor(225, 229, 239);
      doc.roundedRect(x, y, width, 17, 3, 3, "FD");
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      doc.setTextColor(105, 116, 139);
      doc.text(label, x + 4, y + 6);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10.5);
      doc.setTextColor(25, 34, 57);
      doc.text(String(value), x + 4, y + 13);
    };

    addHeader();
    const filename = result.original_filename || result.notebook_name || "Notebook";
    const overallLevel = result.summary?.overall_risk_level || "LOW";
    const highestRisk = Number(result.summary?.highest_risk_percentage || 0);

    section("Analysis overview");
    line(`Notebook: ${filename}`, true);
    line(`Generated: ${new Date().toLocaleString()}`);
    line(`Model version: ${result.model_version || "2.0.0"}`);
    if (dual) {
      line(`Risk mode: Dual ML | Code threshold: ${codeThreshold.toFixed(2)} | Execution threshold: ${executionThreshold.toFixed(2)}`);
    } else {
      line(`Risk threshold: ${Number(result.threshold ?? 0).toFixed(2)}`);
    }

    ensureSpace(24);
    const gap = 4;
    const width = (contentWidth - gap * 2) / 3;
    metric("Code cells", result.total_code_cells ?? allCells.length, margin, cursorY, width);
    metric("Cells flagged", result.cells_above_threshold ?? 0, margin + width + gap, cursorY, width);
    metric("Highest risk", `${highestRisk.toFixed(2)}% ${overallLevel}`, margin + (width + gap) * 2, cursorY, width);
    cursorY += 24;

    section("Risk distribution");
    [["High risk", distribution.HIGH], ["Medium risk", distribution.MEDIUM], ["Low risk", distribution.LOW]].forEach(([label, count]) => {
      line(`${label}: ${count} cells (${allCells.length ? ((count / allCells.length) * 100).toFixed(1) : "0.0"}%)`);
    });

    if (dual) {
      section("Dual-risk model summary");
      line(`Code risk — High: ${codeSummary.high_risk_cells ?? 0}, Medium: ${codeSummary.medium_risk_cells ?? 0}, Low: ${codeSummary.low_risk_cells ?? 0}`);
      line(`Execution risk — High: ${executionSummary.high_risk_cells ?? 0}, Medium: ${executionSummary.medium_risk_cells ?? 0}, Low: ${executionSummary.low_risk_cells ?? 0}`);
    }

    section("Cells requiring review");
    line("Each flagged cell includes the model signal and the same review guidance shown in the dashboard.", false);

    [...allCells]
      .sort((a, b) => getCombinedRisk(b, dual).percentage - getCombinedRisk(a, dual).percentage)
      .slice(0, 20)
      .forEach((cell) => {
        const risk = getCombinedRisk(cell, dual);
        const codeRisk = getRisk(cell, "code");
        const executionRisk = getRisk(cell, "execution");
        const explanation = getRiskExplanation(cell, dual);

        const drivers =
          explanation.drivers?.length
            ? explanation.drivers.join(" • ")
            : "No specific textual signal was returned by the analyzer.";

        const driverLines = doc.splitTextToSize(
          drivers,
          contentWidth - 42
        );
        const actionLines = doc.splitTextToSize(
          explanation.action || "Review the cell before relying on its output.",
          contentWidth - 42
        );

        const headerHeight = 13;
        const driversHeight = Math.min(driverLines.length, 3) * 3.7 + 7;
        const actionHeight = Math.min(actionLines.length, 3) * 3.7 + 10;
        const boxHeight = headerHeight + driversHeight + actionHeight + 4;

        ensureSpace(boxHeight + 4);

        doc.setFillColor(250, 251, 255);
        doc.setDrawColor(225, 229, 239);
        doc.roundedRect(
          margin,
          cursorY - 4,
          contentWidth,
          boxHeight,
          3,
          3,
          "FD"
        );

        doc.setFont("helvetica", "bold");
        doc.setFontSize(9);
        doc.setTextColor(25, 34, 57);
        doc.text(
          `Cell #${cell.cell_number}`,
          margin + 4,
          cursorY + 2
        );

        doc.setFont("helvetica", "bold");
        doc.setFontSize(7.2);
        doc.setTextColor(91, 61, 245);
        doc.text(
          dual
            ? `Combined ${risk.percentage.toFixed(2)}% | Code ${codeRisk.percentage.toFixed(2)}% | Execution ${executionRisk.percentage.toFixed(2)}%`
            : `${risk.percentage.toFixed(2)}% | ${risk.level}`,
          margin + 32,
          cursorY + 2
        );

        cursorY += 7;

        doc.setFont("helvetica", "bold");
        doc.setFontSize(6.8);
        doc.setTextColor(91, 61, 245);
        doc.text("WHY FLAGGED", margin + 4, cursorY);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(7.1);
        doc.setTextColor(82, 95, 118);
        doc.text(
          driverLines.slice(0, 3),
          margin + 4,
          cursorY + 4
        );

        cursorY += driversHeight;

        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(232, 234, 241);
        doc.roundedRect(
          margin + 4,
          cursorY - 2,
          contentWidth - 8,
          actionHeight - 2,
          2,
          2,
          "FD"
        );

        doc.setFont("helvetica", "bold");
        doc.setFontSize(6.8);
        doc.setTextColor(35, 45, 64);
        doc.text(
          "REVIEW SUGGESTION",
          margin + 8,
          cursorY + 3
        );

        doc.setFont("helvetica", "normal");
        doc.setFontSize(7);
        doc.setTextColor(103, 114, 137);
        doc.text(
          actionLines.slice(0, 3),
          margin + 8,
          cursorY + 7
        );

        cursorY += actionHeight + 3;
      });

    ensureSpace(12);
    doc.setDrawColor(225, 229, 239);
    doc.line(margin, cursorY, pageWidth - margin, cursorY);
    cursorY += 6;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7.5);
    doc.setTextColor(125, 135, 154);
    doc.text("NotebookGuardian AI — Predictions are probabilistic and intended for review support.", margin, cursorY);

    const safeName = String(filename).replace(/\.ipynb$/i, "").replace(/[^a-z0-9_-]+/gi, "_").replace(/^_+|_+$/g, "") || "notebook";
    doc.save(`${safeName}_NotebookGuardian_Report.pdf`);
  }


  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <main className="app-shell">


      {/* =================================================
          TOPBAR
      ================================================= */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">

            <ShieldCheck
              size={29}
              strokeWidth={2.2}
            />

          </div>


          <div>

            <div className="brand-title">

              Notebook
              <span>Guardian</span>
              <b>AI</b>

            </div>


            <div className="brand-subtitle">

              Predict notebook risk before it becomes a failure

            </div>

          </div>

        </div>


        <nav className="main-nav">

          <a
            className="active"
            href="#home"
          >
            Home
          </a>

          <a href="#features">
            Features
          </a>

          <a href="#how-it-works">
            How it Works
          </a>

          <a href="#about">
            About
          </a>

        </nav>


        <div className="header-actions">

          <div className="model-pill">

            <BrainCircuit size={18} />

            <div>

              <strong>
                Model v
                {result?.model_version ||
                  "2.0"}
              </strong>

              <span>
                {dual
                  ? "Dual Risk ML"
                  : "ML Classifier"}
              </span>

            </div>

          </div>


          <a
            className="icon-button"
            href="https://github.com/"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub"
          >
            <Github size={19} />
          </a>

        </div>

      </header>


      {/* =================================================
          HERO
      ================================================= */}

      <section
        className="hero"
        id="home"
      >

        <div className="hero-visual hero-visual-left">

          <div className="jupyter-book">
            <span>Jupyter</span>
          </div>

        </div>


        <div className="hero-visual hero-visual-right">

          <div className="code-window">

            <span />
            <span />
            <span />

            <div className="python-dot">
              Py
            </div>

            <div className="warning-dot">
              !
            </div>

          </div>

        </div>


        <div className="hero-eyebrow">

          <Sparkles size={15} />

          ML-powered notebook risk intelligence

        </div>


        <h1>

          Analyze your Jupyter notebook

          <span>
            before the next run.
          </span>

        </h1>


        <p>

          Upload a{" "}
          <strong>.ipynb</strong>{" "}
          file and NotebookGuardian scores each code cell using trained machine-learning models, highlighting code and execution risk patterns.

        </p>

      </section>


      {/* =================================================
          UPLOAD
      ================================================= */}

      <section className="workspace">


        <div className="upload-panel">

          <div
            className={`drop-zone ${
              dragging ? "dragging" : ""
            } ${
              file ? "has-file" : ""
            }`}
            onDragEnter={(event) => {

              event.preventDefault();

              setDragging(true);

            }}
            onDragOver={(event) =>
              event.preventDefault()
            }
            onDragLeave={() =>
              setDragging(false)
            }
            onDrop={handleDrop}
            onClick={() =>
              inputRef.current?.click()
            }
          >

            <input
              ref={inputRef}
              type="file"
              accept=".ipynb"
              hidden
              onChange={(event) =>
                validateAndSetFile(
                  event.target.files?.[0]
                )
              }
            />


            <div className="upload-icon-wrap">

              <div className="upload-icon">

                {file ? (
                  <FileCode2 size={38} />
                ) : (
                  <UploadCloud size={38} />
                )}

              </div>


              {file && (
                <div className="ready-check">

                  <CheckCircle2 size={18} />

                </div>
              )}

            </div>


            {file ? (
              <>

                <div className="selected-file-row">

                  <h3>
                    {file.name}
                  </h3>

                  <CheckCircle2 size={18} />

                </div>


                <p>
                  Notebook selected and ready for analysis.
                </p>


                <div className="file-meta">

                  <span>

                    <File size={14} />

                    Size{" "}
                    {formatBytes(
                      file.size
                    )}

                  </span>


                  <span>

                    <FileCode2 size={14} />

                    Type .ipynb

                  </span>


                  <span className="ready">

                    <i />

                    Ready to analyze

                  </span>

                </div>


                <span className="upload-helper">

                  Click to choose another notebook

                </span>

              </>
            ) : (
              <>

                <h3>
                  Drop your notebook here
                </h3>

                <p>
                  or click to browse your computer
                </p>

                <span className="upload-helper">
                  Only .ipynb files are supported
                </span>

              </>
            )}

          </div>


          <div className="action-row">

            <button
              className="primary-button"
              onClick={analyzeNotebook}
              disabled={
                !file || loading
              }
            >

              {loading ? (
                <>
                  <LoaderCircle
                    className="spin"
                    size={18}
                  />

                  Analyzing notebook...
                </>
              ) : (
                <>
                  <Sparkles size={18} />

                  Analyze notebook

                  <span className="arrow">
                    →
                  </span>
                </>
              )}

            </button>


            <button
              className="secondary-button"
              onClick={resetAll}
            >

              <RotateCcw size={17} />

              Reset

            </button>

          </div>

          {loading && (
            <div
              className="analysis-status-card"
              role="status"
              aria-live="polite"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                marginTop: "14px",
                padding: "12px 14px",
                border: "1px solid #ddd9ff",
                borderRadius: "12px",
                background: "linear-gradient(135deg, #faf9ff 0%, #f6f9ff 100%)"
              }}
            >
              <div
                style={{
                  width: "34px",
                  height: "34px",
                  flex: "0 0 34px",
                  display: "grid",
                  placeItems: "center",
                  borderRadius: "10px",
                  background: "#ebe8ff",
                  color: "#5b3df5"
                }}
              >
                <LoaderCircle className="spin" size={18} />
              </div>

              <div style={{ minWidth: 0 }}>
                <strong
                  style={{
                    display: "block",
                    fontSize: "12px",
                    color: "#172033",
                    marginBottom: "3px"
                  }}
                >
                  Analyzing your notebook
                </strong>

                <span
                  style={{
                    display: "block",
                    fontSize: "11px",
                    lineHeight: 1.5,
                    color: "#64748b"
                  }}
                >
                  Parsing cells, extracting features, and running the dual-risk models...
                </span>
              </div>
            </div>
          )}

          {error && (
            <div
              className="error-box"
              role="alert"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
                flexWrap: "wrap"
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "9px",
                  minWidth: 0,
                  flex: "1 1 260px"
                }}
              >
                <XCircle size={18} />

                <span>
                  {error}
                </span>
              </div>

              {file && (
                <button
                  type="button"
                  onClick={analyzeNotebook}
                  disabled={loading}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                    minHeight: "32px",
                    padding: "7px 11px",
                    border: "1px solid #f0b8b8",
                    borderRadius: "8px",
                    background: "#ffffff",
                    color: "#b42318",
                    fontSize: "11px",
                    fontWeight: 700,
                    cursor: loading ? "not-allowed" : "pointer"
                  }}
                >
                  <RotateCcw size={13} />
                  Retry analysis
                </button>
              )}
            </div>
          )}

        </div>


        {/* =================================================
            INFO
        ================================================= */}

        <aside
          className="info-panel"
          id="how-it-works"
        >

          <div className="info-header">

            <BrainCircuit size={22} />

            How scoring works

          </div>


          <div className="info-step">

            <span>01</span>

            <div>

              <strong>
                Notebook parsing
              </strong>

              <p>
                Code cells and execution metadata are extracted.
              </p>

            </div>

            <div className="step-icon">

              <FileCode2 size={18} />

            </div>

          </div>


          <div className="info-step">

            <span>02</span>

            <div>

              <strong>
                Feature intelligence
              </strong>

              <p>
                AST structure, mutation patterns and ML operations are scored.
              </p>

            </div>

            <div className="step-icon">

              <BrainCircuit size={18} />

            </div>

          </div>


          <div className="info-step">

            <span>03</span>

            <div>

              <strong>
                Dual risk prediction
              </strong>

              <p>
                Separate models estimate code and execution risk.
              </p>

            </div>

            <div className="step-icon">

              <BarChart3 size={18} />

            </div>

          </div>


          <div className="risk-legend">

            <div>

              <i className="dot high" />

              High: 75%+

            </div>


            <div>

              <i className="dot medium" />

              Medium: threshold to 74.99%

            </div>


            <div>

              <i className="dot low" />

              Low: below threshold

            </div>

          </div>

        </aside>

      </section>


      {/* =================================================
          FEATURES
      ================================================= */}

      <section
        className="feature-strip"
        id="features"
      >

        <FeatureCard
          icon={ShieldCheck}
          title="Early Risk Detection"
          text="Catch issues before execution to avoid failures."
          tone="blue"
        />


        <FeatureCard
          icon={Code2}
          title="Code Risk"
          text="Identify risky code structure and patterns."
          tone="orange"
        />


        <FeatureCard
          icon={BrainCircuit}
          title="Dual ML Models"
          text="Separate code and execution risk scoring."
          tone="purple"
        />


        <FeatureCard
          icon={LockKeyhole}
          title="Privacy First"
          text="Local analysis keeps your notebook data safe."
          tone="aqua"
        />

      </section>


      {/* =================================================
          RESULTS
      ================================================= */}

      {result && (

        <section
          className="results-section"
          id="results"
        >


          {/* RESULT HEADER */}

          <div className="results-heading">

            <div>

              <p className="section-kicker">
                Analysis complete
              </p>


              <h2>
                {result.original_filename ||
                  result.notebook_name}
              </h2>


              <p>

                {result.total_code_cells} code cells analyzed ·{" "}

                {dual
                  ? `Code threshold ${codeThreshold.toFixed(
                      2
                    )} · Execution threshold ${executionThreshold.toFixed(
                      2
                    )}`
                  : `Threshold ${Number(
                      result.threshold
                    ).toFixed(2)}`}

              </p>

            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "9px",
                flexWrap: "wrap",
                justifyContent: "flex-end"
              }}
            >
              <button
                className="secondary-button"
                type="button"
                onClick={startNewAnalysis}
                disabled={loading}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  minHeight: "40px",
                  padding: "9px 14px",
                  border: "1px solid #d9d4ff",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, #ffffff 0%, #f8f7ff 100%)",
                  color: "#5b3df5",
                  fontSize: "12px",
                  fontWeight: 700,
                  whiteSpace: "nowrap",
                  cursor: loading ? "not-allowed" : "pointer",
                  boxShadow: "0 4px 12px rgba(91, 61, 245, 0.08)",
                  transition: "all 0.2s ease"
                }}
              >
                <RotateCcw size={15} />
                Analyze another notebook
              </button>

              <button
                className="export-report-button"
                type="button"
                onClick={exportReport}
              >
                <Download size={16} />
                Export PDF
              </button>
            </div>


            <div
              className={`overall-score ${riskClass(
                result.summary
                  ?.overall_risk_level
              )}`}
            >

              <span>

                {dual
                  ? "Overall risk signal"
                  : "Overall risk"}

              </span>


              <strong>
                {riskPercent.toFixed(2)}%
              </strong>


              <RiskBadge
                level={
                  result.summary
                    ?.overall_risk_level
                }
              />

            </div>

          </div>


          {/* =================================================
              DUAL SUMMARY
          ================================================= */}

          {dual ? (
            <>

              <div className="dual-summary-banner">

                <div>

                  <div className="dual-summary-title">

                    <BrainCircuit size={21} />

                    Dual-risk analysis

                  </div>


                  <p>

                    Two independent ML models evaluate code structure and execution-state risk.

                  </p>

                </div>


                <div className="threshold-pills">

                  <span>

                    Code{" "}

                    <b>
                      {codeThreshold.toFixed(2)}
                    </b>

                  </span>


                  <span>

                    Execution{" "}

                    <b>
                      {executionThreshold.toFixed(
                        2
                      )}
                    </b>

                  </span>

                </div>

              </div>


              <div className="summary-grid">

                <SummaryCard
                  icon={Code2}
                  label="Code risk high"
                  value={
                    codeSummary.high_risk_cells ??
                    "—"
                  }
                  hint="Code-pattern alerts"
                  tone="danger"
                />


                <SummaryCard
                  icon={Activity}
                  label="Execution risk high"
                  value={
                    executionSummary.high_risk_cells ??
                    "—"
                  }
                  hint="State/execution alerts"
                  tone="warning"
                />


                <SummaryCard
                  icon={CheckCircle2}
                  label="Cells analyzed"
                  value={
                    result.total_code_cells
                  }
                  hint="Notebook code cells"
                  tone="success"
                />


                <SummaryCard
                  icon={BrainCircuit}
                  label="Dual risk cells"
                  value={
                    result.cells_above_threshold ??
                    allCells.length
                  }
                  hint="Cells surfaced for review"
                  tone="neutral"
                />

              </div>

            </>
          ) : (

            <div className="summary-grid">

              <SummaryCard
                icon={AlertTriangle}
                label="High risk"
                value={
                  result.summary
                    ?.high_risk_cells
                }
                hint="Immediate review recommended"
                tone="danger"
              />


              <SummaryCard
                icon={Activity}
                label="Medium risk"
                value={
                  result.summary
                    ?.medium_risk_cells
                }
                hint="Worth reviewing before execution"
                tone="warning"
              />


              <SummaryCard
                icon={CheckCircle2}
                label="Low risk"
                value={
                  result.summary
                    ?.low_risk_cells
                }
                hint="No strong risk pattern detected"
                tone="success"
              />


              <SummaryCard
                icon={BrainCircuit}
                label="Above threshold"
                value={
                  result.cells_above_threshold
                }
                hint={`out of ${result.total_code_cells} code cells`}
                tone="neutral"
              />

            </div>

          )}


          {/* =================================================
              PREMIUM DASHBOARD
          ================================================= */}

          <div className="premium-dashboard">


            {/* =================================================
                RISK DISTRIBUTION
            ================================================= */}

            <section className="distribution-panel">

              <div className="distribution-header">

                <div>

                  <p className="section-kicker">
                    Risk overview
                  </p>

                  <h3>
                    Risk distribution
                  </h3>

                </div>


                <div className="distribution-total">

                  <strong>
                    {allCells.length}
                  </strong>

                  <span>
                    cells
                  </span>

                </div>

              </div>


              <div className="distribution-chart">

                {[
                  [
                    "HIGH",
                    "High risk",
                    "high"
                  ],
                  [
                    "MEDIUM",
                    "Medium risk",
                    "medium"
                  ],
                  [
                    "LOW",
                    "Low risk",
                    "low"
                  ]
                ].map(
                  ([key, label, tone]) => {

                    const count =
                      distribution[key];


                    const width =
                      (count /
                        maxDistribution) *
                      100;


                    const percentage =
                      allCells.length
                        ? (
                            (count /
                              allCells.length) *
                            100
                          ).toFixed(1)
                        : "0.0";


                    return (
                      <div
                        className="distribution-row"
                        key={key}
                      >

                        <div className="distribution-label">

                          <span
                            className={`distribution-dot ${tone}`}
                          />


                          <strong>
                            {label}
                          </strong>


                          <span>
                            {count}
                          </span>

                        </div>


                        <div className="distribution-track">

                          <span
                            className={`distribution-fill ${tone}`}
                            style={{
                              width: `${width}%`
                            }}
                          />

                        </div>


                        <div className="distribution-percent">

                          {percentage}%

                        </div>

                      </div>
                    );
                  }
                )}

              </div>

            </section>


            {/* =================================================
                SEARCH + FILTER
            ================================================= */}

            <section className="cell-control-panel">

              <div className="control-top">

                <div>

                  <p className="section-kicker">
                    Explore analysis
                  </p>

                  <h3>
                    Find specific cells
                  </h3>

                </div>


                <span className="filtered-count">

                  {filteredCells.length} shown

                </span>

              </div>


              {/* SEARCH */}

              <div className="search-box">

                <Search size={18} />


                <input
                  type="text"
                  placeholder="Search cell number, code or detected signal..."
                  value={searchQuery}
                  onChange={(event) =>
                    setSearchQuery(
                      event.target.value
                    )
                  }
                />


                {searchQuery && (

                  <button
                    onClick={() =>
                      setSearchQuery("")
                    }
                    aria-label="Clear search"
                  >

                    <X size={15} />

                  </button>

                )}

              </div>


              {/* FILTERS */}

              <div className="filter-row">

                {[
                  [
                    "ALL",
                    "All"
                  ],
                  [
                    "HIGH",
                    "High"
                  ],
                  [
                    "MEDIUM",
                    "Medium"
                  ],
                  [
                    "LOW",
                    "Low"
                  ],
                  [
                    "DUAL",
                    "Risk flagged"
                  ]
                ].map(
                  ([value, label]) => (

                    <button
                      key={value}
                      className={
                        riskFilter === value
                          ? "filter-button active"
                          : "filter-button"
                      }
                      onClick={() =>
                        setRiskFilter(
                          value
                        )
                      }
                    >

                      {label}


                      {value !== "DUAL" && (

                        <span>

                          {value ===
                          "HIGH"
                            ? distribution.HIGH
                            : value ===
                              "MEDIUM"
                            ? distribution.MEDIUM
                            : value ===
                              "LOW"
                            ? distribution.LOW
                            : allCells.length}

                        </span>

                      )}

                    </button>

                  )
                )}

              </div>

              {/* RISK LEGEND */}
              <div
                className="risk-legend"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "10px",
                  marginTop: "12px",
                  padding: "10px 12px",
                  border: "1px solid #e7e5f7",
                  borderRadius: "10px",
                  background: "#fbfbff"
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "7px",
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#59657a"
                  }}
                >
                  <Info size={14} color="#5b3df5" />
                  Risk levels
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "8px 14px"
                  }}
                >
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "5px",
                      fontSize: "10.5px",
                      color: "#526174"
                    }}
                  >
                    <i
                      style={{
                        width: "7px",
                        height: "7px",
                        borderRadius: "50%",
                        background: "#ef4444"
                      }}
                    />
                    High ≥ 75%
                  </span>

                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "5px",
                      fontSize: "10.5px",
                      color: "#526174"
                    }}
                  >
                    <i
                      style={{
                        width: "7px",
                        height: "7px",
                        borderRadius: "50%",
                        background: "#f59e0b"
                      }}
                    />
                    Medium ≥ {Math.round((dual ? Math.min(codeThreshold, executionThreshold) : Number(result.threshold ?? 0)) * 100)}%
                  </span>

                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "5px",
                      fontSize: "10.5px",
                      color: "#526174"
                    }}
                  >
                    <i
                      style={{
                        width: "7px",
                        height: "7px",
                        borderRadius: "50%",
                        background: "#10b981"
                      }}
                    />
                    Low below threshold
                  </span>
                </div>
              </div>

            </section>

          </div>


          {/* =================================================
              ANALYSIS GRID
          ================================================= */}

          <div className="analysis-grid">


            {/* =================================================
                CELL LIST
            ================================================= */}

            <section className="risk-list-panel">

              <div className="panel-heading">

                <div>

                  <p className="section-kicker">
                    Priority review
                  </p>

                  <h3>
                    {dual
                      ? "Notebook risk cells"
                      : "Top risky cells"}
                  </h3>

                </div>


                <span className="count-pill">

                  {filteredCells.length} shown

                </span>

              </div>


              <div className="cell-list">

                {filteredCells.length > 0 ? (

                  filteredCells.map(
                    (cell) => (

                      <CellCard
                        key={
                          cell.cell_number
                        }
                        cell={cell}
                        dual={dual}
                        onPreview={
                          setPreviewCell
                        }
                      />

                    )
                  )

                ) : (

                  <div className="empty-filter-state">

                    <Search size={28} />

                    <h4>
                      No matching cells
                    </h4>

                    <p>
                      Try another search term or change the risk filter.
                    </p>


                    <button
                      onClick={() => {

                        setSearchQuery("");

                        setRiskFilter(
                          "ALL"
                        );

                      }}
                    >
                      Clear filters
                    </button>

                  </div>

                )}

              </div>

            </section>


            {/* =================================================
                INSIGHTS
            ================================================= */}

            <aside className="insight-panel">

              <div className="insight-icon">

                <ShieldCheck size={24} />

              </div>


              <h3>

                {dual
                  ? "Dual-risk health summary"
                  : "Notebook health summary"}

              </h3>


              <p>

                {dual
                  ? "NotebookGuardian separates structural code risk from execution-state risk, making it easier to see why a cell needs review."
                  : "NotebookGuardian is designed as an early-warning system. It prioritizes catching risky patterns before execution."}

              </p>


              <div className="health-meter">

                <div className="health-label-row">

                  <span>
                    Cells below threshold
                  </span>


                  <strong>

                    {result.total_code_cells -
                      result.cells_above_threshold}

                    /

                    {result.total_code_cells}

                  </strong>

                </div>


                <div className="health-track">

                  <span
                    style={{
                      width: `${
                        result.total_code_cells
                          ? (
                              (
                                result.total_code_cells -
                                result.cells_above_threshold
                              ) /
                              result.total_code_cells
                            ) * 100
                          : 0
                      }%`
                    }}
                  />

                </div>

              </div>


              <div className="model-note">

                <BrainCircuit size={17} />

                <div>

                  <strong>

                    Model{" "}
                    {result.model_version ||
                      "2.0.0"}

                  </strong>


                  <p>

                    Predictions are probabilistic and intended for review support.

                  </p>

                </div>

              </div>

            </aside>

          </div>

        </section>

      )}


      {/* =================================================
          FOOTER
      ================================================= */}

      <footer id="about">

        <div className="footer-brand">

          <ShieldCheck size={17} />

          NotebookGuardian AI

        </div>


        <span className="footer-love">

          Built for safer and smarter ML workflows

        </span>

      </footer>


      {/* =================================================
          CODE MODAL
      ================================================= */}

      <CodePreviewModal
        cell={previewCell}
        dual={dual}
        onClose={() =>
          setPreviewCell(null)
        }
      />

    </main>
  );
}