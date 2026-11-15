import { useMemo, useState } from "react";
import data from "./data.json";

const REPO = "https://github.com/JesunAhmadUshno/hitl-approval-gate";

const OUTCOME_LABEL = {
  auto_approved: "auto approved",
  approved: "approved",
  rejected: "rejected",
  denied: "denied",
  pending: "pending",
};

function FlowDiagram() {
  return (
    <figure className="diagram-wrap">
      <svg viewBox="0 0 960 500" role="img" aria-label="Diagram of the approval gate flow: a producer submits a request, the policy router reads policy.toml and sends it to the auto, human or deny route, human decisions are made on the decision page or by CLI, and every step is written to the append-only hash chained log" className="diagram">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="d-arrowhead" />
          </marker>
        </defs>
        <rect x="16" y="196" width="150" height="88" rx="8" className="d-box" />
        <text x="36" y="232" className="d-title">Producer</text>
        <text x="36" y="254" className="d-sub">CLI and HTTP API</text>
        <text x="36" y="272" className="d-sub">demo-agent stream</text>

        <line x1="166" y1="240" x2="226" y2="240" className="d-line" markerEnd="url(#arrow)" />

        <rect x="230" y="176" width="196" height="128" rx="8" className="d-box-accent" />
        <text x="250" y="216" className="d-title">Policy router</text>
        <text x="250" y="240" className="d-sub">reads policy.toml</text>
        <text x="250" y="258" className="d-sub">one route per risk class</text>
        <text x="250" y="276" className="d-sub">unlisted class: {data.defaultRoute}</text>

        <path d="M 426 210 C 470 210 470 76 514 76" className="d-line" markerEnd="url(#arrow)" />
        <line x1="426" y1="240" x2="514" y2="240" className="d-line" markerEnd="url(#arrow)" />
        <path d="M 426 270 C 470 270 470 404 514 404" className="d-line" markerEnd="url(#arrow)" />

        <rect x="518" y="40" width="180" height="72" rx="8" className="d-box" />
        <text x="538" y="72" className="d-title">auto route</text>
        <text x="538" y="94" className="d-sub">approved at once</text>

        <rect x="518" y="204" width="180" height="72" rx="8" className="d-box" />
        <text x="538" y="236" className="d-title">human route</text>
        <text x="538" y="258" className="d-sub">waits in the queue</text>

        <rect x="518" y="368" width="180" height="72" rx="8" className="d-box" />
        <text x="538" y="400" className="d-title">deny route</text>
        <text x="538" y="422" className="d-sub">refused at once</text>

        <line x1="698" y1="240" x2="758" y2="240" className="d-line" markerEnd="url(#arrow)" />
        <rect x="762" y="196" width="182" height="88" rx="8" className="d-box" />
        <text x="782" y="232" className="d-title">Human decision</text>
        <text x="782" y="254" className="d-sub">decision page and CLI</text>
        <text x="782" y="272" className="d-sub">approve or reject, with reason</text>

        <path d="M 608 112 C 608 330 330 330 330 380" className="d-line-soft" markerEnd="url(#arrow)" />
        <path d="M 853 284 C 853 350 700 356 560 380" className="d-line-soft" markerEnd="url(#arrow)" />
        <path d="M 608 440 L 608 462" className="d-line-soft" markerEnd="url(#arrow)" />

        <rect x="230" y="384" width="714" height="72" rx="8" className="d-box-graphite" />
        <text x="250" y="416" className="d-title-light">Append-only decision log</text>
        <text x="250" y="438" className="d-sub-light">hash chained, {data.logRecords} records in the simulated run</text>
      </svg>
      <figcaption>Every route ends in the same log.</figcaption>
    </figure>
  );
}

function Explorer() {
  const [selected, setSelected] = useState("all");
  const rows = useMemo(() => {
    if (selected === "all") return data.byRiskClass;
    return data.byRiskClass.filter((r) => r.risk_class === selected);
  }, [selected]);
  const total = rows.reduce((s, r) => s + r.total, 0);
  return (
    <div>
      <div className="filters" role="group" aria-label="Filter the simulated requests by risk class">
        <button type="button" className={selected === "all" ? "filter-btn is-active" : "filter-btn"} onClick={() => setSelected("all")} aria-pressed={selected === "all"}>
          all classes
        </button>
        {data.byRiskClass.map((r) => (
          <button key={r.risk_class} type="button" className={selected === r.risk_class ? "filter-btn is-active" : "filter-btn"} onClick={() => setSelected(r.risk_class)} aria-pressed={selected === r.risk_class}>
            {r.risk_class}
          </button>
        ))}
      </div>
      <p className="explorer-total">Showing {total} of {data.requestCount} SIMULATED requests</p>
      <div className="table-scroll">
        <table className="roomy-table">
          <thead>
            <tr><th scope="col">risk class</th><th scope="col">route</th><th scope="col">requests</th><th scope="col">share</th><th scope="col">outcomes</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const share = Math.round((r.total / data.requestCount) * 1000) / 10;
              const outcomes = Object.entries(r.outcomes).map(([k, v]) => `${OUTCOME_LABEL[k] || k}: ${v}`).join(", ");
              return (
                <tr key={r.risk_class}>
                  <td><code>{r.risk_class}</code></td>
                  <td>{r.route}</td>
                  <td className="num">{r.total}</td>
                  <td>
                    <span className="bar"><span className="bar-fill" style={{ width: `${share}%` }} /></span>
                    <span className="num">{share}%</span>
                  </td>
                  <td>{outcomes}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Metric({ value, label, detail }) {
  return (
    <div className="metric">
      <span className="metric-value num">{value}</span>
      <span className="metric-label">{label}</span>
      <span className="metric-detail">{detail}</span>
    </div>
  );
}

export default function App() {
  const s = data.stats;
  return (
    <div className="page">
      <header className="site-head container">
        <a className="wordmark" href={REPO}>hitl-approval-gate</a>
        <nav aria-label="Repository">
          <a href={REPO}>Repository</a>
          <a href={`${REPO}/blob/main/RESULTS.md`}>Full results</a>
          <a href={`${REPO}/blob/main/APPROVER-GUIDE.md`}>Approver guide</a>
        </nav>
      </header>

      <main>
        <section className="hero container">
          <h1>Agents ask before they act.</h1>
          <p className="lead">A policy file routes each action: auto approval, human decision, or refusal.</p>
          <p className="actions">
            <a className="btn btn-primary" href={REPO}>View the repository</a>
            <a className="btn" href="#simulated">See the simulated results</a>
          </p>
          <FlowDiagram />
        </section>

        <section className="section container" aria-labelledby="policy-h">
          <h2 id="policy-h">Policy routing</h2>
          <p className="section-lede">These routes are read from policy.toml at build time.</p>
          <div className="table-scroll">
            <table className="policy-table">
              <thead><tr><th scope="col">risk class</th><th scope="col">route</th><th scope="col">what it covers</th></tr></thead>
              <tbody>
                {data.policy.map((p) => (
                  <tr key={p.risk_class}><td><code>{p.risk_class}</code></td><td>{p.route}</td><td>{p.description}</td></tr>
                ))}
                <tr><td><code>any unlisted class</code></td><td>{data.defaultRoute}</td><td>Fallback route named by default_route in policy.toml.</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="section container" id="simulated" aria-labelledby="sim-h">
          <h2 id="sim-h">Simulated arm results</h2>
          <p className="sim-banner">SIMULATED: a scripted approver made every decision. These numbers describe the script, not a person.</p>
          <div className="metrics">
            <Metric value={data.routingAccuracy.toFixed(3)} label="SIMULATED routing accuracy" detail={`${data.routingChecked} of ${data.requestCount} requests`} />
            <Metric value={`${s.autoApproveRatePct}%`} label="SIMULATED auto-approve rate" detail={`${s.autoApproved} requests`} />
            <Metric value={`${s.escalationRatePct}%`} label="SIMULATED escalation rate" detail={`${s.humanDecided} sent to the approver`} />
            <Metric value={`${s.denyRatePct}%`} label="SIMULATED deny rate" detail={`${s.denied} refused by policy`} />
            <Metric value={`${s.humanApprovalRatePct}%`} label="SIMULATED approver approval rate" detail={`${s.approved} approved, ${s.rejected} rejected`} />
            <Metric value={`${s.latency.p50} s`} label="SIMULATED latency p50" detail="distribution output" />
            <Metric value={`${s.latency.p90} s`} label="SIMULATED latency p90" detail="distribution output" />
            <Metric value={`${s.latency.p99} s`} label="SIMULATED latency p99" detail="distribution output" />
          </div>
        </section>

        <section className="section container" aria-labelledby="explore-h">
          <h2 id="explore-h">Explore the simulated requests</h2>
          <Explorer />
          <h3 className="subhead">The simulated approver, as specified</h3>
          <div className="table-scroll">
            <table>
              <thead><tr><th scope="col">risk class</th><th scope="col">approval probability</th><th scope="col">delay median</th></tr></thead>
              <tbody>
                {data.approverSpec.map((a) => (
                  <tr key={a.risk_class}><td><code>{a.risk_class}</code></td><td className="num">{a.approveProbability}</td><td className="num">{a.delayMedianSeconds} s</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="note">Delays are lognormal, sigma {data.delaySigma}. Latency is drawn, not observed.</p>
        </section>

        <section className="section container" aria-labelledby="live-h">
          <h2 id="live-h">Live arm: NOT RUN</h2>
          <p className="section-lede">Ready, and not run. No human results exist, and none are claimed here.</p>
          <div className="table-scroll">
            <table className="roomy-table">
              <thead><tr><th scope="col">risk class</th><th scope="col">session requests</th><th scope="col">route</th></tr></thead>
              <tbody>
                {data.liveBreakdown.map((r) => (
                  <tr key={r.risk_class}><td><code>{r.risk_class}</code></td><td className="num">{r.count}</td><td>{r.route}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="note">hitl-gate live loads these {data.liveArm.sessionRequests} requests and serves the decision page. One sitting, about 10 to 15 minutes.</p>
        </section>

        <section className="section container" aria-labelledby="log-h">
          <h2 id="log-h">The log keeps the receipts</h2>
          <p className="section-lede">Each record carries the hash of the record before it.</p>
          <div className="table-scroll">
            <table className="roomy-table">
              <thead><tr><th scope="col">record</th><th scope="col">count or value</th></tr></thead>
              <tbody>
                <tr><td>records in the simulated log</td><td className="num">{data.logRecords}</td></tr>
                <tr><td>requests submitted</td><td className="num">{data.requestCount}</td></tr>
                <tr><td>decisions recorded</td><td className="num">{data.logDecisions}</td></tr>
                <tr><td>first record hash, first 16 characters</td><td><code>{data.firstHash}</code></td></tr>
                <tr><td>last record hash, first 16 characters</td><td><code>{data.lastHash}</code></td></tr>
                <tr><td>chain check</td><td><code>hitl-gate verify-log</code></td></tr>
              </tbody>
            </table>
          </div>
          <p className="note">verify-log recomputes the chain and detects any later edit or deletion.</p>
        </section>
      </main>

      <footer className="site-foot container">
        <p>Claims ceiling: the simulated numbers describe a script, not a person. The human study exists only when the named approver runs the live arm.</p>
        <p><a href={REPO}>hitl-approval-gate on GitHub</a></p>
        <p className="support-links">
          <a className="support-pill" href="https://github.com/sponsors/JesunAhmadUshno">Sponsor this work</a>
          <a className="support-pill" href="https://github.com/sponsors/JesunAhmadUshno">Donate</a>
          <a className="support-pill" href="https://buymeacoffee.com/jesun">Buy Me a Coffee</a>
          <a className="support-pill" href="https://calendly.com/jesunahmadushno/30min">Work with me</a>
        </p>
      </footer>
    </div>
  );
}
