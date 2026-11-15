// Fails the build when src/data.json drifts from RESULTS.md, the frozen
// source record. Every headline figure on the page must appear in
// RESULTS.md with the same value.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(join(here, "..", "src", "data.json"), "utf-8"));
const md = data.resultsMdSnapshot;

const checks = [
  ["request count", String(data.requestCount), md.includes(`${data.requestCount} requests`)],
  ["routing accuracy", data.routingAccuracy.toFixed(3), md.includes(data.routingAccuracy.toFixed(3))],
  ["auto-approve rate", `${data.stats.autoApproveRatePct}%`, md.includes(`${data.stats.autoApproveRatePct}%`)],
  ["escalation rate", `${data.stats.escalationRatePct}%`, md.includes(`${data.stats.escalationRatePct}%`)],
  ["deny rate", `${data.stats.denyRatePct}%`, md.includes(`${data.stats.denyRatePct}%`)],
  ["human approval rate", `${data.stats.humanApprovalRatePct}%`, md.includes(`${data.stats.humanApprovalRatePct}%`)],
  ["latency p50", `${data.stats.latency.p50} s`, md.includes(`| ${data.stats.latency.p50} s |`)],
  ["latency p90", `${data.stats.latency.p90} s`, md.includes(`| ${data.stats.latency.p90} s |`)],
  ["latency p99", `${data.stats.latency.p99} s`, md.includes(`| ${data.stats.latency.p99} s |`)],
  ["live arm not run", data.liveArm.status, md.includes("Live arm: NOT RUN")],
  ["simulated label", data.armLabel, md.includes("SIMULATED")],
];

let failed = 0;
for (const [name, value, ok] of checks) {
  if (!ok) {
    console.error(`check failed: ${name} (${value}) not found in RESULTS.md`);
    failed += 1;
  }
}
if (failed > 0) process.exit(1);
console.log(`check passed: ${checks.length} figures match RESULTS.md`);
