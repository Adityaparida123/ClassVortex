import React from "react";

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderInline(raw: string): React.ReactNode[] {
  const tokens: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*)/g;
  const parts = raw.split(regex);
  parts.forEach((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      tokens.push(
        <strong key={i}>{escapeHtml(part.slice(2, -2))}</strong>
      );
    } else if (part.trim()) {
      tokens.push(<React.Fragment key={i}>{escapeHtml(part)}</React.Fragment>);
    }
  });
  return tokens;
}

/**
 * Minimal, safe Markdown renderer for AI answers.
 *
 * Supported: bold (**text**), bullet lists (- / • lines), and blank-line
 * separated paragraphs. All HTML in the AI output is escaped so the AI can
 * never inject markup.
 */
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
        return (
          <p key={blockIndex} className="whitespace-pre-wrap break-words">
            {lines.map((line, li) => (
              <React.Fragment key={li}>
                {renderInline(line)}
                {li < lines.length - 1 ? <br /> : null}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}