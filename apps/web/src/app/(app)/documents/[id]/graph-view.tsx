"use client";

import type { DocumentGraph } from "@/lib/types";

const TYPE_COLORS: Record<string, string> = {
  Document: "#0f172a",
  Zone: "#2563eb",
  Project: "#7c3aed",
  Organization: "#059669",
  Person: "#db2777",
  ContractRef: "#d97706",
  Amount: "#dc2626",
  Date: "#0891b2",
};

function colorFor(type: string): string {
  return TYPE_COLORS[type] ?? "#64748b";
}

function truncate(label: string, max = 22): string {
  return label.length > max ? `${label.slice(0, max - 1)}…` : label;
}

export function GraphView({ graph }: { graph: DocumentGraph }) {
  const center = graph.nodes.find((n) => n.type === "Document");
  const others = graph.nodes.filter((n) => n.type !== "Document");

  if (!center) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">No graph data yet.</p>;
  }

  const size = 420;
  const mid = size / 2;
  const radius = Math.min(170, 90 + others.length * 6);
  const positioned = others.map((node, i) => {
    const angle = (2 * Math.PI * i) / Math.max(others.length, 1) - Math.PI / 2;
    return {
      ...node,
      x: mid + radius * Math.cos(angle),
      y: mid + radius * Math.sin(angle),
    };
  });

  return (
    <div className="overflow-x-auto">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="mx-auto">
        {positioned.map((node) => (
          <line
            key={`edge-${node.id}`}
            x1={mid}
            y1={mid}
            x2={node.x}
            y2={node.y}
            className="stroke-slate-200 dark:stroke-slate-700"
            strokeWidth={1.5}
          />
        ))}

        {positioned.map((node) => (
          <g key={node.id}>
            <circle cx={node.x} cy={node.y} r={8} fill={colorFor(node.type)} />
            <text
              x={node.x}
              y={node.y + (node.y > mid ? 20 : -14)}
              textAnchor="middle"
              fontSize={11}
              className="fill-slate-700 dark:fill-slate-200"
            >
              <title>{node.label}</title>
              {truncate(node.label, 18)}
            </text>
            <text
              x={node.x}
              y={node.y + (node.y > mid ? 32 : -2)}
              textAnchor="middle"
              fontSize={9}
              className="fill-slate-400 dark:fill-slate-500"
            >
              {node.type}
            </text>
          </g>
        ))}

        <circle cx={mid} cy={mid} r={12} fill={colorFor("Document")} />
        <text
          x={mid}
          y={mid + 26}
          textAnchor="middle"
          fontSize={11}
          fontWeight={600}
          className="fill-slate-900 dark:fill-slate-100"
        >
          <title>{center.label}</title>
          {truncate(center.label, 24)}
        </text>
      </svg>
    </div>
  );
}
