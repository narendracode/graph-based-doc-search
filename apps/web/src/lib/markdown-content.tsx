"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

// Tailwind's preflight reset strips default list markers/spacing from every element,
// so plain <ReactMarkdown content={...} /> renders bullets/numbers-less, cramped
// text. These overrides restore normal-looking prose in both themes.
const COMPONENTS: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noreferrer" className="underline">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-slate-200 px-1 py-0.5 text-xs dark:bg-slate-700">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="mb-2 overflow-x-auto rounded bg-slate-200 p-2 text-xs dark:bg-slate-700 last:mb-0">
      {children}
    </pre>
  ),
  h1: ({ children }) => <h1 className="mb-2 text-base font-semibold">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 text-base font-semibold">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1 text-sm font-semibold">{children}</h3>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-slate-300 pl-2 italic dark:border-slate-600">
      {children}
    </blockquote>
  ),
};

export function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="text-sm leading-relaxed [&>*:last-child]:mb-0">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={COMPONENTS}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
