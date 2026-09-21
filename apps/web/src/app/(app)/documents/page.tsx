"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  STATUS_LABELS,
  type AutocompleteItem,
  type DocumentListItem,
  type DocumentType,
  type Project,
  type SearchResultItem,
  type Zone,
} from "@/lib/types";
import { provenanceText } from "@/lib/format";
import { ChatPanel } from "./chat-panel";

type Mode = "search" | "ai";

export default function DocumentsPage() {
  const [mode, setMode] = useState<Mode>("search");
  const [zones, setZones] = useState<Zone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.get<Zone[]>("/zones").then(setZones).catch(() => {});
    api.get<Project[]>("/projects").then(setProjects).catch(() => {});
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center gap-2">
        <ModeButton active={mode === "search"} onClick={() => setMode("search")}>
          Search
        </ModeButton>
        <ModeButton active={mode === "ai"} onClick={() => setMode("ai")}>
          AI Mode
        </ModeButton>
      </div>

      {mode === "search" ? (
        <SearchView zones={zones} projects={projects} />
      ) : (
        <ChatPanel />
      )}
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-brand text-white dark:bg-brand-light dark:text-ink"
          : "border border-slate-300 bg-white text-slate-600 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-300"
      }`}
    >
      {children}
    </button>
  );
}

function SearchView({ zones, projects }: { zones: Zone[]; projects: Project[] }) {
  const [query, setQuery] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [docTypeId, setDocTypeId] = useState("");
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [suggestions, setSuggestions] = useState<AutocompleteItem[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResultItem[] | null>(null);
  const [browseResults, setBrowseResults] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const hasQuery = query.trim().length > 0;

  useEffect(() => {
    api.get<DocumentType[]>("/document-types").then(setDocumentTypes).catch(() => {});
  }, []);

  useEffect(() => {
    if (hasQuery) return; // filters only apply to browse mode
    const params = new URLSearchParams();
    if (zoneId) params.set("zone_id", zoneId);
    if (projectId) params.set("project_id", projectId);
    if (docTypeId) params.set("doc_type_id", docTypeId);
    api
      .get<DocumentListItem[]>(`/documents?${params.toString()}`)
      .then(setBrowseResults)
      .catch(() => {});
  }, [zoneId, projectId, docTypeId, hasQuery]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setSuggestions([]);
      setSearchResults(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const [ac, results] = await Promise.all([
          api.get<AutocompleteItem[]>(`/search/autocomplete?q=${encodeURIComponent(query)}`),
          api.get<SearchResultItem[]>(`/search?q=${encodeURIComponent(query)}`),
        ]);
        setSuggestions(ac);
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      } finally {
        setLoading(false);
      }
    }, 350);
  }, [query]);

  const emptyState = useMemo(() => {
    if (hasQuery) return searchResults !== null && searchResults.length === 0 && !loading;
    return browseResults.length === 0;
  }, [hasQuery, searchResults, browseResults, loading]);

  return (
    <div>
      <div className="relative mb-4">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          placeholder="Search by keyword or meaning — e.g. 'contract value for Delhi Metro'"
          className="w-full rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 focus:border-slate-500 focus:outline-none dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
        />
        {showSuggestions && suggestions.length > 0 && (
          <ul className="absolute z-10 mt-1 w-full rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800">
            {suggestions.map((s) => (
              <li key={s.id}>
                <Link
                  href={s.url}
                  className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  {s.filename}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      {!hasQuery && (
        <div className="mb-4 flex flex-wrap gap-3">
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
            value={zoneId}
            onChange={(e) => setZoneId(e.target.value)}
          >
            <option value="">All zones</option>
            {zones.map((z) => (
              <option key={z.id} value={z.id}>
                {z.name}
              </option>
            ))}
          </select>
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
            value={docTypeId}
            onChange={(e) => setDocTypeId(e.target.value)}
          >
            <option value="">All types</option>
            {documentTypes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {emptyState && (
        <p className="rounded-lg border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
          No documents found.
        </p>
      )}

      {hasQuery ? (
        <ul className="space-y-3">
          {(searchResults ?? []).map((r) => (
            <li
              key={r.id}
              className="rounded-xl border border-slate-200 bg-white shadow-sm p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="mb-1 flex items-center justify-between">
                <Link
                  href={r.url}
                  className="text-sm font-medium text-slate-900 hover:underline dark:text-slate-100"
                >
                  {r.filename}
                </Link>
                <span className="text-xs uppercase tracking-wide text-slate-400 dark:text-slate-500">
                  {r.doc_type_name}
                </span>
              </div>
              <p className="text-sm text-slate-600 line-clamp-3 dark:text-slate-300">{r.snippet}</p>
              <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">{provenanceText(r)}</p>
            </li>
          ))}
        </ul>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white shadow-sm dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
          {browseResults.map((d) => (
            <li key={d.id} className="flex items-center justify-between px-4 py-3 text-sm">
              <div>
                <Link
                  href={d.url}
                  className="font-medium text-slate-900 hover:underline dark:text-slate-100"
                >
                  {d.filename}
                </Link>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {d.zone_name} • {d.project_name} • {d.doc_type_name}
                </p>
                <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{provenanceText(d)}</p>
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400">{STATUS_LABELS[d.status]}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
