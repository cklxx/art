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

export function App() {
  const [paper, setPaper] = useState({
    title: "Transformer-based Image Generation",
    url: "",
    abstract: "We explore diffusion-guided transformers for rapid media generation and evaluation.",
  });
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [prompts, setPrompts] = useState<PromptRow[]>([]);
  const [running, setRunning] = useState<string>("");

  const analysisDisabled = useMemo(
    () => !paper.title.trim() || !paper.abstract.trim(),
    [paper.abstract, paper.title]
  );

  useEffect(() => {
    setAnalysis(null);
    setPrompts([]);
  }, [paper.title, paper.abstract, paper.url]);

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
