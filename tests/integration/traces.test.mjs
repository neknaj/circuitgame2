import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { chromium } from "playwright";

assert.ok(process.env.NCG2_CLI_PATH && process.env.NCG2_WEB_PATH,
  "NCG2_CLI_PATH と NCG2_WEB_PATH に CLI と Web のチェックアウト先を指定する。");
const cli = resolve(process.env.NCG2_CLI_PATH);
const web = resolve(process.env.NCG2_WEB_PATH);
const ncg2 = join(cli, "target", "debug", process.platform === "win32" ? "ncg2.exe" : "ncg2");
const component = join(cli, "target", "wasm32-wasip2", "debug", "ncg2.wasm");


function run(file, args, cwd, options = {}) {
  return execFileSync(file, args, { cwd, encoding: "utf8", timeout: 30_000, ...options }).trim();
}

function coreSource(cwd) {
  const metadata = JSON.parse(run("cargo", ["metadata", "--locked", "--format-version", "1"], cwd, {
    // GUI の別ターゲット向け依存も含めて、Core の取り込み方を検査する。
    maxBuffer: 8 * 1024 * 1024,
  }));
  const core = metadata.packages.filter(({ name }) => name === "circuitgame2-core");
  assert.equal(core.length, 1);
  const source = core[0].source;
  assert.equal(typeof source, "string", "Core の依存先を Git のコミットに固定する。");
  assert.match(source, /^git\+https:\/\/github\.com\/neknaj\/circuitgame2-core\?rev=([0-9a-f]{40})#\1$/);
  if (process.env.NCG2_CORE_SHA) {
    assert.equal(source.split("#")[1], process.env.NCG2_CORE_SHA);
  }
  return source;
}

function cliTrace(cwd, frames, vram) {
  const args = ["run", "--project", "circuitgame2.toml"];
  if (vram) args.push("--vram", vram);
  for (const frame of frames) args.push("--input", frame);
  const native = run(ncg2, args, cwd).split(/\r?\n/);
  const wasi = run("wasmtime", ["run", "--dir=.", component, ...args], cwd).split(/\r?\n/);
  assert.deepEqual(wasi, native);
  return native;
}

async function browserTrace(page, folder, frames, vram) {
  const project = page.locator("#project");
  await page.waitForFunction(() => !document.querySelector("#project").disabled);
  await project.setInputFiles(folder);
  const tick = page.getByRole("button", { name: "1 tick 進める" });
  await page.waitForFunction(
    () => document.querySelector("#running-source").textContent.includes("circuitgame2.toml"),
  );
  const switches = page.getByRole("checkbox");
  const trace = [];
  const record = async (index) => {
    const output = (await page.locator("#outputs .led").allTextContents()).join("");
    assert.ok(await page.locator("#outputs").isVisible());
    assert.equal(await page.locator("#position").textContent(), `tick ${index}、出力 ${output}`);
    assert.equal(await page.locator("#status").textContent(), "");
    const row = [index, output];
    if (vram) {
      assert.ok(await page.locator("#vram-bits").isVisible());
      assert.equal(await page.locator("#vram-name").inputValue(), vram);
      row.push(await page.locator("#vram-bits").textContent());
    }
    trace.push(row.join(" "));
  };

  await record(0);
  for (const [index, frame] of frames.entries()) {
    assert.equal(await switches.count(), frame.length);
    for (const [bit, value] of Array.from(frame).entries()) {
      await switches.nth(bit).setChecked(value === "1");
    }
    await tick.click();
    await record(index + 1);
  }
  await page.getByRole("button", { name: "リセット" }).click();
  await record(0);
  assert.equal(trace.pop(), trace[0]);
  assert.equal(await page.locator("#inputs input:checked").count(), 0);
  return trace;
}

function serveSite() {
  const assets = new Map([
    ["/", ["site/index.html", "text/html; charset=utf-8"]],
    ["/style.css", ["site/style.css", "text/css; charset=utf-8"]],
    ["/main.js", ["site/main.js", "text/javascript; charset=utf-8"]],
    ["/project.js", ["site/project.js", "text/javascript; charset=utf-8"]],
    ["/examples/main.ncg2", ["site/examples/main.ncg2", "text/plain; charset=utf-8"]],
    ["/pkg/circuitgame2_web.js", ["site/pkg/circuitgame2_web.js", "text/javascript; charset=utf-8"]],
    ["/pkg/circuitgame2_web_bg.wasm", ["site/pkg/circuitgame2_web_bg.wasm", "application/wasm"]],
    ["/workbench/", ["crates/gui/web/index.html", "text/html; charset=utf-8"]],
    ["/workbench/start.js", ["crates/gui/web/start.js", "text/javascript; charset=utf-8"]],
    ["/workbench/pkg/circuitgame2_gui.js", ["crates/gui/web/pkg/circuitgame2_gui.js", "text/javascript; charset=utf-8"]],
    ["/workbench/pkg/circuitgame2_gui_bg.wasm", ["crates/gui/web/pkg/circuitgame2_gui_bg.wasm", "application/wasm"]],
  ]);
  return createServer(async (request, response) => {
    const asset = assets.get(request.url);
    if (!asset) {
      response.writeHead(404).end();
      return;
    }
    try {
      const contents = await readFile(join(web, asset[0]));
      response.writeHead(200, { "Content-Type": asset[1] }).end(contents);
    } catch {
      response.writeHead(500).end();
    }
  });
}

test("共有プロジェクトの実行とブラウザーでの読み込みを確認する", async (t) => {
  assert.equal(coreSource(web), coreSource(cli));
  const server = serveSite();
  await new Promise((ok, fail) => {
    server.once("error", fail);
    server.listen(0, "127.0.0.1", ok);
  });
  t.after(() => new Promise((ok, fail) => server.close((error) => error ? fail(error) : ok())));
  const base = `http://127.0.0.1:${server.address().port}/`;
  // GPU を備えない CI でも、ループバックで配信する共通画面を WebGL で描画する。
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader"] });
  const fixtures = fileURLToPath(new URL("./fixtures/", import.meta.url));
  const cases = [
    { name: "project", frames: ["0", "1"], expected: ["0 0", "1 1", "2 0"] },
    { name: "vram", frames: ["1101", "1000"], vram: "screen", expected: ["0 00 0000", "1 00 0010", "2 10 0010"] },
    {
      name: "oscillator",
      folder: join(fixtures, "oscillator"),
      frames: ["0", "0", "1", "1"],
      expected: ["0 00", "1 10", "2 00", "3 11", "4 01"],
    },
    {
      name: "sr-latch",
      folder: join(fixtures, "sr-latch"),
      frames: ["10", "00", "01", "01", "00"],
      expected: ["0 00", "1 10", "2 10", "3 00", "4 01", "5 01"],
    },
  ];
  try {
    for (const { name, folder = join(cli, "examples", name), frames, vram, expected } of cases) {
      await t.test(name, async () => {
        const native = cliTrace(folder, frames, vram);
        assert.deepEqual(native, expected);
        const page = await browser.newPage();
        try {
          await page.goto(base);
          assert.deepEqual(await browserTrace(page, folder, frames, vram), native);
        } finally {
          await page.close();
        }
      });
    }
    await t.test("共通 GUI はフォルダーのエラーを表示し、開き直せる", async () => {
      const page = await browser.newPage();
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      try {
        await page.goto(new URL("workbench/", base).href);
        const folder = page.getByLabel("Open project folder");
        await folder.waitFor();
        const canvas = page.locator("canvas#workbench");
        const initial = await canvas.screenshot();

        await folder.setInputFiles(join(web, "site", "examples"));
        await page.waitForFunction(() => document.querySelector("#project-status")
          .textContent.includes("circuitgame2.toml がない"));

        await folder.setInputFiles(join(cli, "examples", "project"));
        await page.waitForFunction(() => document.querySelector("#project-status").textContent === "");
        assert.equal(await page.locator("#status").isVisible(), false);
        assert.notDeepEqual(await canvas.screenshot(), initial);
        assert.deepEqual(errors, []);
      } finally {
        await page.close();
      }
    });
  } finally {
    await browser.close();
  }
});
