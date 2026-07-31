// POST /api/sandbox/run
// Receives { files: Record<string, { content, language }> }
// Returns { html: string (full standalone page), logs: string[] }
export const runtime = "nodejs";

type FileMap = Record<string, { content: string; language: string }>;

function buildStandaloneHtml(files: FileMap): string {
  const html = files["index.html"]?.content ?? "<h1>No index.html found</h1>";
  const css  = files["style.css"]?.content  ?? files["styles.css"]?.content ?? "";
  const js   = Object.entries(files)
    .filter(([n]) => (n.endsWith(".js") || n.endsWith(".ts") || n.endsWith(".jsx") || n.endsWith(".tsx")) && n !== "index.html")
    .map(([, f]) => f.content)
    .join("\n\n");

  // Inject inline <style> and <script> so the srcDoc iframe is self-contained
  let doc = html;

  if (css) {
    // Replace <link rel="stylesheet" ...> with inline <style>
    doc = doc.replace(/<link[^>]+rel=["']stylesheet["'][^>]*>/gi, "");
    doc = doc.replace("</head>", `<style>\n${css}\n</style>\n</head>`);
  }

  if (js) {
    // Replace <script src="..."> references with inline script
    doc = doc.replace(/<script[^>]+src=["'][^"']+["'][^>]*><\/script>/gi, "");
    // Wrap in try/catch and forward console.log to parent
    const wrappedJs = `
(function() {
  const _log = console.log.bind(console);
  const _warn = console.warn.bind(console);
  const _err = console.error.bind(console);
  function postLog(type, ...args) {
    try { window.parent.postMessage({ type: '__sandbox_log__', logType: type, text: args.map(String).join(' ') }, '*'); } catch(_) {}
    if (type === 'error') _err(...args);
    else if (type === 'warn') _warn(...args);
    else _log(...args);
  }
  console.log = (...a) => postLog('log', ...a);
  console.warn = (...a) => postLog('warn', ...a);
  console.error = (...a) => postLog('error', ...a);
  try {
${js}
  } catch(e) { postLog('error', 'Runtime error: ' + e.message); }
})();`;
    doc = doc.replace("</body>", `<script>\n${wrappedJs}\n</script>\n</body>`);
  }

  return doc;
}

export async function POST(request: Request) {
  try {
    const { files } = (await request.json()) as { files: FileMap };

    if (!files || typeof files !== "object") {
      return Response.json({ error: "files object required" }, { status: 400 });
    }

    const html = buildStandaloneHtml(files);

    return Response.json({
      html,
      logs: [`Built ${Object.keys(files).length} file(s) successfully.`],
    });
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : "build error" },
      { status: 500 }
    );
  }
}
