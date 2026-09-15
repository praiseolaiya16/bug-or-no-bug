import { useMemo } from "react";
import Prism from "prismjs";
import "prismjs/components/prism-python";

const LINE_HEIGHT = 21;

/**
 * Syntax-highlighted, line-numbered source view. Renders the whole file as
 * a single Prism-highlighted block (so multi-line tokens like docstrings
 * stay intact), then overlays a highlight band and gutter marks positioned
 * purely by line-number math — the same technique Prism's own
 * line-highlight plugin uses, chosen so we don't have to re-tokenize
 * per line.
 *
 * @param {{ code: string, bugLine: number|null, staticLines: Set<number>, llmLines: Set<number> }} props
 */
function CodeBlock({ code, bugLine, staticLines, llmLines }) {
  const html = useMemo(() => Prism.highlight(code, Prism.languages.python, "python"), [code]);
  const lines = useMemo(() => code.split("\n"), [code]);

  return (
    <div className="code-block">
      <div className="code-scroll">
        <div className="code-gutter">
          {lines.map((_, index) => {
            const lineNumber = index + 1;
            const hasStatic = staticLines.has(lineNumber);
            const hasLlm = llmLines.has(lineNumber);
            return (
              <div
                key={lineNumber}
                className={`gutter-row${lineNumber === bugLine ? " gutter-row-bug" : ""}`}
                style={{ height: LINE_HEIGHT }}
              >
                <span className="gutter-number">{lineNumber}</span>
                <span className="gutter-marks">
                  {hasStatic && <span className="mark mark-static" title="Static analysis flagged this line" />}
                  {hasLlm && <span className="mark mark-llm" title="LLM flagged this line" />}
                </span>
              </div>
            );
          })}
        </div>
        <div className="code-body">
          {bugLine && (
            <div
              className="bug-line-band"
              style={{ top: (bugLine - 1) * LINE_HEIGHT, height: LINE_HEIGHT }}
              aria-hidden="true"
            />
          )}
          <pre className="code-pre" style={{ lineHeight: `${LINE_HEIGHT}px` }}>
            <code
              className="language-python"
              // eslint-disable-next-line react/no-danger
              dangerouslySetInnerHTML={{ __html: html }}
            />
          </pre>
        </div>
      </div>
    </div>
  );
}

export default CodeBlock;
