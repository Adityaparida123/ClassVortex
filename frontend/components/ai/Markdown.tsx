import React from "react";

/**
 * Minimal Markdown renderer for AI answers.
 *
 * Supported: bold (**text**), bullet lines (- / •, ordered 1.), and paragraph
 * blocks. Everything is rendered through React text nodes, which React escapes
 * natively (`<`, `>`, `&`) — the same mechanism that keeps JSX safe. We must
 * NOT manually HTML-escape the content: React does not decode entities inside
 * text nodes, so pre-escaping would surface literal `&#39;` / `&quot;` to the
 * user (the exact bug this replaces).
 */
function renderInline(raw: string): React.ReactNode[] {
  const tokens: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*)/g;
  const parts = raw.split(regex);
  parts.forEach((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      tokens.push(<strong key={i}>{part.slice(2, -2)}</strong>);
    } else if (part.trim()) {
      tokens.push(<React.Fragment key={i}>{part}</React.Fragment>);
    }
  });
  return tokens;
}

function renderParagraph(lines: string[]): React.ReactNode {
  return (
    <p className="whitespace-pre-wrap break-words">
      {lines.map((line, li) => (
        <React.Fragment key={li}>
          {renderInline(line)}
          {li < lines.length - 1 ? <br /> : null}
        </React.Fragment>
      ))}
    </p>
  );
}

export default function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/).filter((b) => b.trim().length > 0);

  return (
    <div className="space-y-2">
      {blocks.map((block, blockIndex) => {
        const lines = block.split("\n").filter((l) => l.trim().length > 0);
        if (lines.every((l) => /^\s*(?:[-•*])\s+/.test(l) || /^\s*\d+\.\s+/.test(l))) {
          const ordered = lines.every((l) => /^\s*\d+\.\s+/.test(l));
          return ordered ? (
            <ol key={blockIndex} className="list-decimal pl-6 space-y-1">
              {lines.map((line, li) => (
                <li key={li}>{renderInline(line.replace(/^\s*\d+\.\s+/, ""))}</li>
              ))}
            </ol>
          ) : (
            <ul key={blockIndex} className="list-disc pl-6 space-y-1">
              {lines.map((line, li) => (
                <li key={li}>{renderInline(line.replace(/^\s*(?:[-•*])\s+/, ""))}</li>
              ))}
            </ul>
          );
        }
        return renderParagraph(lines);
      })}
    </div>
  );
}