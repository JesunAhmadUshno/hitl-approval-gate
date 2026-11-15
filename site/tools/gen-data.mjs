// Generates src/data.json from the repo record, so the page cannot drift
// from RESULTS.md, results/simulated_arm.json, results/simulated-log.jsonl
// and policy.toml. Run by the build before vite.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");

const arm = JSON.parse(readFileSync(join(root, "results", "simulated_arm.json"), "utf-8"));
const resultsMd = readFileSync(join(root, "RESULTS.md"), "utf-8");
const policyToml = readFileSync(join(root, "policy.toml"), "utf-8");
const logLines = readFileSync(join(root, "results", "simulated-log.jsonl"), "utf-8")
  .split("\n")
  .filter((l) => l.trim().length > 0);

const requests = new Map();
const decisions = new Map();
for (const line of logLines) {
  const rec = JSON.parse(line);
  if (rec.event === "request_submitted") requests.set(rec.data.id, rec.data);
  else decisions.set(rec.data.id, rec.data);
}

const breakdown = {};
for (const [id, req] of requests) {
  const cls = req.risk_class;
  if (!breakdown[cls]) breakdown[cls] = { risk_class: cls, route: req.route, total: 0, outcomes: {} };
  breakdown[cls].total += 1;
  const status = decisions.get(id)?.status || "pending";
  breakdown[cls].outcomes[status] = (breakdown[cls].outcomes[status] || 0) + 1;
}
const byRiskClass = Object.values(breakdown).sort((a, b) => b.total - a.total);

// Policy classes parsed from policy.toml
const policy = [];
const classRe = /\[classes\.([a-z_]+)\]\s*\nroute = "([a-z]+)"\s*\ndescription = "([^"]+)"/g;
let m;
while ((m = classRe.exec(policyToml)) !== null) {
  policy.push({ risk_class: m[1], route: m[2], description: m[3] });
}
const defaultRoute = (policyToml.match(/default_route = "([a-z]+)"/) || [])[1] || "human";

const liveSession = JSON.parse(readFileSync(join(root, "scripts", "live_session_requests.json"), "utf-8"));
const liveCounts = {};
for (const r of liveSession.requests) liveCounts[r.risk_class] = (liveCounts[r.risk_class] || 0) + 1;
const routeByClass = Object.fromEntries(policy.map((p) => [p.risk_class, p.route]));
const liveBreakdown = Object.entries(liveCounts)
  .map(([risk_class, count]) => ({ risk_class, count, route: routeByClass[risk_class] || defaultRoute }))
  .sort((a, b) => b.count - a.count);

const parsedLog = logLines.map((l) => JSON.parse(l));
const firstHash = parsedLog[0]?.hash?.slice(0, 16) || "";
const lastHash = parsedLog[parsedLog.length - 1]?.hash?.slice(0, 16) || "";

const pct = (v) => Math.round(v * 1000) / 10;

const data = {
  generatedFrom: ["RESULTS.md", "results/simulated_arm.json", "results/simulated-log.jsonl", "policy.toml"],
  seed: arm.seed,
  armLabel: arm.arm,
  requestCount: arm.request_count,
  routingAccuracy: arm.routing_accuracy,
  routingChecked: arm.routing_checked,
  stats: {
    total: arm.stats.total,
    autoApproved: arm.stats.by_status.auto_approved,
    approved: arm.stats.by_status.approved,
    rejected: arm.stats.by_status.rejected,
    denied: arm.stats.by_status.denied,
    autoApproveRatePct: pct(arm.stats.auto_approve_rate),
    escalationRatePct: pct(arm.stats.escalation_rate),
    denyRatePct: pct(arm.stats.deny_rate),
    humanDecided: arm.stats.human_decided,
    humanApprovalRatePct: pct(arm.stats.human_approval_rate),
    latency: arm.stats.human_latency_seconds,
  },
  approverSpec: Object.keys(arm.approver_spec.approve_probability).map((cls) => ({
    risk_class: cls,
    approveProbability: arm.approver_spec.approve_probability[cls],
    delayMedianSeconds: arm.approver_spec.delay_median_seconds[cls],
  })),
  delaySigma: arm.approver_spec.delay_sigma,
  submitIntervalSeconds: arm.approver_spec.submit_interval_seconds,
  byRiskClass,
  policy,
  defaultRoute,
  logRecords: logLines.length,
  logDecisions: decisions.size,
  firstHash,
  lastHash,
  liveBreakdown,
  liveArm: { status: "NOT RUN", sessionRequests: liveSession.requests.length },
  resultsMdSnapshot: resultsMd,
};

writeFileSync(join(here, "..", "src", "data.json"), JSON.stringify(data, null, 2));
console.log(`data.json written: ${data.requestCount} requests, ${byRiskClass.length} risk classes, ${logLines.length} log records`);
