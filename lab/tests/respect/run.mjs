// Gedeelde testsuite, deel 2 (in de respect-container): voert de geplande Arazzo-runs uit
// met Redocly Respect. Leest results/raw/<stack>/respect-jobs.json (van tests/run.py) en
// schrijft per run de JSON-uitvoer en een log. Faalt nooit zelf: tests/rapport.py
// beoordeelt de uitkomst.
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";

const cli = "tests/respect/node_modules/@redocly/cli/bin/cli.js";
const jobs = JSON.parse(readFileSync(process.argv[2], "utf8"));

for (const job of jobs) {
  const args = [cli, "respect", job.arazzo, "--json-output", job.uitvoer];
  for (const [naam, url] of Object.entries(job.servers ?? {})) args.push("--server", `${naam}=${url}`);
  for (const [naam, waarde] of Object.entries(job.inputs ?? {})) args.push("--input", `${naam}=${waarde}`);
  if (job.severity) args.push("--severity", job.severity);
  const start = Date.now();
  const r = spawnSync(process.execPath, args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  writeFileSync(job.log, `${r.stdout ?? ""}\n${r.stderr ?? ""}`);
  console.log(`${job.naam}: exitcode ${r.status} in ${((Date.now() - start) / 1000).toFixed(1)}s`);
}
