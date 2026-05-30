import { execSync, spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const BACKEND_PORT = 8000;

function pickPythonCommand() {
  const venvWin = join(rootDir, ".venv", "Scripts", "python.exe");
  const venvUnix = join(rootDir, ".venv", "bin", "python");

  if (existsSync(venvWin)) {
    return [venvWin];
  }
  if (existsSync(venvUnix)) {
    return [venvUnix];
  }
  if (process.platform === "win32") {
    return ["py", "-3.13"];
  }
  return ["python3"];
}

function freePort(port) {
  if (process.platform !== "win32") {
    return;
  }

  try {
    const output = execSync(`netstat -ano | findstr :${port} | findstr LISTENING`, {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    });

    const pids = new Set();
    for (const line of output.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const pid = Number(trimmed.split(/\s+/).at(-1));
      if (pid > 0) {
        pids.add(pid);
      }
    }

    for (const pid of pids) {
      try {
        execSync(`taskkill /F /PID ${pid}`, { stdio: "ignore" });
        console.log(`[backend] Freed port ${port} (PID ${pid})`);
      } catch {
        // Process may already be gone while socket metadata is stale.
      }
    }
  } catch {
    // Port is already free.
  }
}

freePort(BACKEND_PORT);

const [command, ...prefixArgs] = pickPythonCommand();
const args = [
  ...prefixArgs,
  "-m",
  "uvicorn",
  "backend.app.main:app",
  "--host",
  "127.0.0.1",
  "--port",
  String(BACKEND_PORT),
];

const child = spawn(command, args, {
  cwd: rootDir,
  stdio: "inherit",
  shell: false,
  env: {
    ...process.env,
    DISABLE_SAFETENSORS_CONVERSION: "1",
    TRANSFORMERS_VERBOSITY: "error",
    TQDM_DISABLE: "1",
  },
});

child.on("exit", (code) => {
  process.exit(code ?? 1);
});
