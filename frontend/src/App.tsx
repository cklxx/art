import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type Analysis = {
  summary: string;
  key_points: string[];
  image_prompts: string[];
  recommended_style: string;
};

type PromptRow = {
  id: string;
  prompt: string;
  feedback?: string;
  imageUrl?: string;
  note?: string;
  status?: "idle" | "running" | "done";
};

type Roadmap = {
  completed: string[];
  in_progress: string[];
  upcoming: string[];
  technical_plan: string[];
  risks: string[];
  industry_practices: string[];
  optimization_focus: string[];
  testing_tips: string[];
};

type AdapterSpec = {
  name: string;
  status: string;
  description: string;
  setup: string[];
  example?: string;
};

type AdapterCatalog = {
  stores: AdapterSpec[];
  llms: AdapterSpec[];
};

type TraceEvent = {
  name: string;
  duration_ms: number;
  attributes: Record<string, string>;
};

type TraceStep = {
  name: string;
  start_ms: number;
  end_ms: number;
  duration_ms: number;
  attributes: Record<string, string>;
};

type TraceTimeline = {
  task_id: string;
  total_ms: number;
  events: TraceStep[];
};

type RetrievalBenchmarkCaseResult = {
  case_id: string;
  precision_at_k: number;
  recall_at_k: number;
  relevant_found: string[];
};

type BenchmarkRun = {
  adapter: string;
  duration_ms: number;
  suite: {
    macro_precision: number;
    macro_recall: number;
    results: RetrievalBenchmarkCaseResult[];
  };
};

type AutomatedBenchmarkSummary = {
  runs: BenchmarkRun[];
  macro_precision: number;
  macro_recall: number;
  history?: BenchmarkRun[];
};

type RetrievalHit = {
  id: string;
  score: number;
  summary: string;
  tags: string[];
  modality: string;
  sources?: string[];
};

type KnowledgeSlice = {
  id: string;
  summary: string;
  highlights: string[];
  modality: string;
  tags: string[];
  source_refs: string[];
};

type KnowledgeBundle = {
  slices: KnowledgeSlice[];
};

type OrchestrationStep = {
  name: string;
  summary: string;
  notes?: Record<string, unknown>;
};

type OrchestrationReport = {
  hits: RetrievalHit[];
  synthesis: KnowledgeBundle;
  evaluation: Record<string, unknown>;
  steps: OrchestrationStep[];
};

export function App() {
  const [paper, setPaper] = useState({
    title: "Transformer-based Image Generation",
    url: "",
    abstract: "We explore diffusion-guided transformers for rapid media generation and evaluation.",
  });
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [prompts, setPrompts] = useState<PromptRow[]>([]);
  const [running, setRunning] = useState<string>("");

  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [adapters, setAdapters] = useState<AdapterCatalog | null>(null);
  const [traces, setTraces] = useState<TraceEvent[]>([]);
  const [timeline, setTimeline] = useState<TraceTimeline[]>([]);
  const [retrieveQuery, setRetrieveQuery] = useState("multimodal knowledge bundles");
  const [retrievalHits, setRetrievalHits] = useState<RetrievalHit[]>([]);
  const [panelLoading, setPanelLoading] = useState<string>("");
  const [adapterInput, setAdapterInput] = useState(
    "baseline_bow,tag_bias,source_bias"
  );
  const [benchSummary, setBenchSummary] = useState<AutomatedBenchmarkSummary | null>(null);
  const [orchestrateGoal, setOrchestrateGoal] = useState(
    "Rank roadmap items for the next demo"
  );
  const [orchestrateContext, setOrchestrateContext] = useState(
    "Roadmap covers adapters, orchestration demos, and retrieval benchmarks."
  );
  const [orchestration, setOrchestration] = useState<OrchestrationReport | null>(null);

  const analysisDisabled = useMemo(
    () => !paper.title.trim() || !paper.abstract.trim(),
    [paper.abstract, paper.title]
  );

  useEffect(() => {
    refreshMeta();
    refreshTraces();
    refreshTimeline();
  }, []);

  useEffect(() => {
    setAnalysis(null);
    setPrompts([]);
  }, [paper.title, paper.abstract, paper.url]);

  const refreshMeta = async () => {
    try {
      const [roadmapRes, adapterRes] = await Promise.all([
        fetch(`${API_URL}/roadmap`),
        fetch(`${API_URL}/adapters`),
      ]);
      setRoadmap(await roadmapRes.json());
      setAdapters(await adapterRes.json());
    } catch (err) {
      console.error("Failed to refresh meta", err);
    }
  };

  const refreshTraces = async () => {
    try {
      const res = await fetch(`${API_URL}/traces/recent?limit=12`);
      setTraces(await res.json());
    } catch (err) {
      console.error("Failed to load traces", err);
    }
  };

  const refreshTimeline = async () => {
    try {
      const res = await fetch(`${API_URL}/traces/timeline?limit=24`);
      setTimeline(await res.json());
    } catch (err) {
      console.error("Failed to load timeline", err);
    }
  };

  const analyzePaper = async () => {
    setRunning("analyze");
    const res = await fetch(`${API_URL}/review/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(paper),
    });
    const data: Analysis = await res.json();
    setAnalysis(data);
    setPrompts(
      data.image_prompts.map((prompt, idx) => ({
        id: `prompt-${idx + 1}`,
        prompt,
        status: "idle",
      }))
    );
    setRunning("");
  };

  const triggerImages = async (targetPrompts?: PromptRow[]) => {
    const toSend = targetPrompts ?? prompts;
    if (!toSend.length) return;
    setPrompts((prev) =>
      prev.map((row) =>
        toSend.find((p) => p.id === row.id)
          ? { ...row, status: "running" }
          : row
      )
    );

    const res = await fetch(`${API_URL}/review/images`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompts: toSend.map((p) => ({ id: p.id, prompt: p.prompt, feedback: p.feedback })),
        style: analysis?.recommended_style,
      }),
    });

    const data = await res.json();
    const updates: Record<string, (typeof prompts)[number]> = {};
    toSend.forEach((p, idx) => {
      const updated = data.images?.[idx];
      updates[p.id] = {
        ...p,
        imageUrl: updated?.url ?? p.imageUrl,
        note: updated?.note,
        status: "done",
      };
    });

    setPrompts((prev) => prev.map((row) => updates[row.id] ?? row));
  };

  const addPrompt = () => {
    setPrompts((prev) => [
      ...prev,
      {
        id: `prompt-${prev.length + 1}`,
        prompt: "New visual angle: highlight limitations or future work.",
        status: "idle",
      },
    ]);
  };

  const runRetrieval = async () => {
    if (!retrieveQuery.trim()) return;
    setPanelLoading("retrieval");
    const res = await fetch(`${API_URL}/retrieve/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: retrieveQuery }),
    });
    const data = await res.json();
    setRetrievalHits(data.hits ?? []);
    setPanelLoading("");
  };

  const runAutomatedBenchmark = async () => {
    setPanelLoading("benchmark");
    const adapters = adapterInput
      .split(",")
      .map((a) => a.trim())
      .filter(Boolean);
    const res = await fetch(`${API_URL}/retrieve/benchmark/automated`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ adapters, track: true }),
    });
    setBenchSummary(await res.json());
    setPanelLoading("");
  };

  const runOrchestration = async () => {
    setPanelLoading("orchestrate");
    const bundle: KnowledgeBundle = {
      slices: [
        {
          id: "context-1",
          summary: orchestrateContext,
          highlights: [orchestrateContext],
          modality: "text",
          tags: ["demo", "orchestration"],
          source_refs: [],
        },
      ],
    };

    const res = await fetch(`${API_URL}/orchestrate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: orchestrateGoal, bundle }),
    });
    setOrchestration(await res.json());
    refreshTimeline();
    setPanelLoading("");
  };

  return (
    <main className="page" data-testid="app-root">
      <header>
        <div>
          <p className="eyebrow">Paper → Analysis → Image Review</p>
          <h1>Auto paper analysis & image review</h1>
          <p className="lede">
            Feed a paper, let the worker flow summarize it, generate visual prompts, and iterate on
            review images with feedback-driven regeneration.
          </p>
        </div>
        <div className="badge">Backend: FastAPI + Google GenAI default</div>
      </header>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Execution radar</p>
            <h2>Roadmap, adapters, observability</h2>
            <p className="muted">
              Track delivered milestones, available adapters, and the latest traces without leaving the UI.
            </p>
          </div>
          <div className="actions">
            <button className="ghost" onClick={refreshMeta}>Refresh roadmap</button>
            <button className="ghost" onClick={() => refreshTraces()}>Refresh traces</button>
            <button className="ghost" onClick={() => refreshTimeline()}>Replay spans</button>
          </div>
        </div>

        <div className="meta-grid">
          <div className="meta-card">
            <p className="eyebrow">Completed</p>
            <ul>
              {(roadmap?.completed ?? []).slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="meta-card">
            <p className="eyebrow">In progress</p>
            <ul>
              {(roadmap?.in_progress ?? []).slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="meta-card">
            <p className="eyebrow">Upcoming</p>
            <ul>
              {(roadmap?.upcoming ?? []).slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="meta-card">
            <p className="eyebrow">Risks</p>
            <ul>
              {(roadmap?.risks ?? ["Model coverage depends on available free/community tiers."]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="meta-grid">
          <div className="meta-card">
            <p className="eyebrow">Industry practices</p>
            <ul>
              {(roadmap?.industry_practices ?? []).slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="meta-card">
            <p className="eyebrow">Optimization focus</p>
            <ul>
              {(roadmap?.optimization_focus ?? []).slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="meta-card">
            <p className="eyebrow">Technical plan</p>
            <ul>
              {(roadmap?.technical_plan ?? []).slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="meta-card">
            <p className="eyebrow">Testing tips</p>
            <ul>
              {(roadmap?.testing_tips ?? []).slice(0, 4).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="adapter-row">
          <div className="adapter-column">
            <div className="adapter-header">
              <p className="eyebrow">Store adapters</p>
              <span className="pill">{adapters?.stores.length ?? 0} options</span>
            </div>
            <div className="spec-grid">
              {(adapters?.stores ?? []).map((spec) => (
                <div key={spec.name} className="spec-card">
                  <div className="spec-head">
                    <strong>{spec.name}</strong>
                    <span className={`status status-${spec.status}`}>{spec.status}</span>
                  </div>
                  <p className="muted">{spec.description}</p>
                  <ul>
                    {spec.setup.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                  {spec.example && <code>{spec.example}</code>}
                </div>
              ))}
            </div>
          </div>
          <div className="adapter-column">
            <div className="adapter-header">
              <p className="eyebrow">LLM adapters</p>
              <span className="pill">{adapters?.llms.length ?? 0} options</span>
            </div>
            <div className="spec-grid">
              {(adapters?.llms ?? []).map((spec) => (
                <div key={spec.name} className="spec-card">
                  <div className="spec-head">
                    <strong>{spec.name}</strong>
                    <span className={`status status-${spec.status}`}>{spec.status}</span>
                  </div>
                  <p className="muted">{spec.description}</p>
                  <ul>
                    {spec.setup.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                  {spec.example && <code>{spec.example}</code>}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="observability">
          <div className="trace-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Traces</p>
                <h3>Recent spans</h3>
              </div>
              <button className="ghost" onClick={refreshTraces}>Reload</button>
            </div>
            <div className="trace-list">
              {traces.length === 0 && <p className="muted">No traces yet. Run a request to populate.</p>}
              {traces.map((trace, idx) => (
                <div key={`${trace.name}-${idx}`} className="trace-row">
                  <div>
                    <strong>{trace.name}</strong>
                    <p className="muted">{Object.entries(trace.attributes).map(([k, v]) => `${k}: ${v}`).join(" · ")}</p>
                  </div>
                  <span className="pill">{trace.duration_ms.toFixed(2)} ms</span>
                </div>
              ))}
            </div>
          </div>
          <div className="trace-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Benchmarks</p>
                <h3>Automated retrieval runs</h3>
              </div>
              <button className="ghost" onClick={runAutomatedBenchmark}>
                {panelLoading === "benchmark" ? "Running..." : "Run now"}
              </button>
            </div>
            <input
              value={adapterInput}
              onChange={(e) => setAdapterInput(e.target.value)}
              placeholder="Adapters (comma separated)"
            />
            {benchSummary && (
              <div className="benchmark-grid">
                <div className="meta-card">
                  <p className="eyebrow">Macro P/R</p>
                  <strong>
                    {benchSummary.macro_precision.toFixed(3)} / {benchSummary.macro_recall.toFixed(3)}
                  </strong>
                  <p className="muted">Averaged across adapters</p>
                </div>
                <div className="meta-card">
                  <p className="eyebrow">History</p>
                  <ul>
                    {(benchSummary.history ?? []).slice(-4).map((run, idx) => (
                      <li key={`${run.adapter}-${idx}`}>
                        {run.adapter}: {run.suite.macro_precision.toFixed(2)} / {run.suite.macro_recall.toFixed(2)}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            <div className="trace-list">
              {!benchSummary && <p className="muted">Run to compare adapters over the canned corpus.</p>}
              {(benchSummary?.runs ?? []).map((run) => (
                <div key={run.adapter} className="trace-row">
                  <div>
                    <strong>{run.adapter}</strong>
                    <p className="muted">
                      Precision {run.suite.macro_precision.toFixed(2)} · Recall {run.suite.macro_recall.toFixed(2)}
                    </p>
                  </div>
                  <span className="pill">{run.duration_ms.toFixed(1)} ms</span>
                </div>
              ))}
            </div>
          </div>
          <div className="trace-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Replay</p>
                <h3>Grouped timelines</h3>
              </div>
              <button className="ghost" onClick={refreshTimeline}>Reload</button>
            </div>
            <div className="trace-list">
              {timeline.length === 0 && <p className="muted">No grouped traces yet. Run a request to populate.</p>}
              {timeline.map((tl) => (
                <div key={tl.task_id} className="timeline-card">
                  <div className="timeline-head">
                    <strong>{tl.task_id}</strong>
                    <span className="pill">{tl.total_ms.toFixed(2)} ms</span>
                  </div>
                  <div className="timeline-steps">
                    {tl.events.map((event, idx) => (
                      <div key={`${event.name}-${idx}`} className="timeline-step">
                        <div>
                          <p className="eyebrow">{event.start_ms.toFixed(1)} → {event.end_ms.toFixed(1)} ms</p>
                          <strong>{event.name}</strong>
                          <p className="muted">{Object.entries(event.attributes).map(([k, v]) => `${k}: ${v}`).join(" · ")}</p>
                        </div>
                        <span className="pill">{event.duration_ms.toFixed(2)} ms</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="trace-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Orchestration</p>
                <h3>Replay + custom goals</h3>
              </div>
              <button className="ghost" onClick={runOrchestration}>
                {panelLoading === "orchestrate" ? "Running..." : "Run orchestration"}
              </button>
            </div>
            <input
              value={orchestrateGoal}
              onChange={(e) => setOrchestrateGoal(e.target.value)}
              placeholder="Goal"
            />
            <textarea
              value={orchestrateContext}
              onChange={(e) => setOrchestrateContext(e.target.value)}
              rows={3}
              placeholder="Context to index into the orchestration demo"
            />
            {orchestration && (
              <div className="timeline-card">
                <div className="timeline-head">
                  <strong>Evaluation</strong>
                  <span className="pill">Coverage {Number(orchestration.evaluation?.coverage ?? 0).toFixed(2)}</span>
                </div>
                <div className="timeline-steps">
                  {orchestration.steps.map((step, idx) => (
                    <div key={`${step.name}-${idx}`} className="timeline-step">
                      <div>
                        <p className="eyebrow">{step.name}</p>
                        <strong>{step.summary}</strong>
                        <p className="muted">{Object.entries(step.notes ?? {}).map(([k, v]) => `${k}: ${String(v)}`).join(" · ")}</p>
                      </div>
                    </div>
                  ))}
                  {orchestration.hits.length > 0 && (
                    <div className="timeline-step">
                      <div>
                        <p className="eyebrow">Hits</p>
                        <strong>{orchestration.hits.map((h) => h.id).join(", ")}</strong>
                        <p className="muted">Scores peak at {Math.max(...orchestration.hits.map((h) => h.score)).toFixed(2)}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="trace-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Retrieval</p>
                <h3>Sandbox query</h3>
              </div>
              <button className="ghost" onClick={runRetrieval}>
                {panelLoading === "retrieval" ? "Searching..." : "Run query"}
              </button>
            </div>
            <input
              value={retrieveQuery}
              onChange={(e) => setRetrieveQuery(e.target.value)}
              placeholder="Query indexed bundles"
            />
            <div className="list-grid">
              {retrievalHits.length === 0 && <p className="muted">No hits yet. Index a bundle then search.</p>}
              {retrievalHits.map((hit) => (
                <div key={hit.id} className="list-item">
                  <strong>{hit.summary}</strong>
                  <p className="muted">Tags: {hit.tags.join(", ") || "none"}</p>
                  <p className="muted">Modality: {hit.modality}</p>
                  <span className="pill">Score: {hit.score.toFixed(3)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Step 1</p>
            <h2>Provide a paper</h2>
            <p className="muted">Title + abstract (URL optional). Google models are used by default.</p>
          </div>
          <button
            className="primary"
            data-testid="analyze-button"
            onClick={analyzePaper}
            disabled={analysisDisabled || running === "analyze"}
          >
            {running === "analyze" ? "Analyzing..." : "Analyze for visuals"}
          </button>
        </div>
        <label>
          Title
          <input
            value={paper.title}
            onChange={(e) => setPaper({ ...paper, title: e.target.value })}
            placeholder="Paper title"
          />
        </label>
        <label>
          URL (optional)
          <input
            value={paper.url}
            onChange={(e) => setPaper({ ...paper, url: e.target.value })}
            placeholder="https://arxiv.org/abs/..."
          />
        </label>
        <label>
          Abstract / notes
          <textarea
            value={paper.abstract}
            onChange={(e) => setPaper({ ...paper, abstract: e.target.value })}
            rows={4}
          />
        </label>
      </section>

      {analysis && (
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Step 2</p>
              <h2>Auto analysis</h2>
              <p className="muted">Summary, key points, and initial figure prompts.</p>
            </div>
            <span className="pill">Style: {analysis.recommended_style}</span>
          </div>
          <div className="summary" data-testid="analysis-summary">
            {analysis.summary}
          </div>
          <div className="list-grid">
            {analysis.key_points.map((point, idx) => (
              <div key={idx} className="list-item">
                <strong>Key point {idx + 1}</strong>
                <p>{point}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {prompts.length > 0 && (
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Step 3</p>
              <h2>Image review queue</h2>
              <p className="muted">Edit prompts, add feedback, regenerate single or batched images.</p>
            </div>
            <div className="actions">
              <button className="ghost" onClick={addPrompt}>+ Add prompt</button>
              <button className="primary" data-testid="generate-all" onClick={() => triggerImages()}>
                Generate all
              </button>
            </div>
          </div>

          <div className="prompts">
            {prompts.map((row) => (
              <div key={row.id} className="prompt-card" data-testid="prompt-card">
                <div className="prompt-header">
                  <strong>{row.id}</strong>
                  <button
                    className="ghost"
                    data-testid="regenerate-button"
                    onClick={() => triggerImages([row])}
                  >
                    {row.status === "running" ? "Generating..." : "Regenerate"}
                  </button>
                </div>
                <textarea
                  value={row.prompt}
                  onChange={(e) =>
                    setPrompts((prev) =>
                      prev.map((p) => (p.id === row.id ? { ...p, prompt: e.target.value } : p))
                    )
                  }
                  rows={3}
                />
                <input
                  placeholder="Feedback (optional)"
                  value={row.feedback ?? ""}
                  onChange={(e) =>
                    setPrompts((prev) =>
                      prev.map((p) => (p.id === row.id ? { ...p, feedback: e.target.value } : p))
                    )
                  }
                />
                {row.imageUrl && (
                  <div className="image-preview" data-testid="image-preview">
                    <img src={row.imageUrl} alt={row.prompt} />
                    <p className="muted">{row.note || "Generated"}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
