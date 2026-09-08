"use client";

import { useState } from "react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { api } from "@/lib/api";

interface ImportSheetsModalProps {
  show: boolean;
  onClose: () => void;
  setImportState: (fn: (prev: any) => any) => void;
  importState: any;
}

export default function ImportSheetsModal({
  show,
  onClose,
  setImportState,
  importState,
}: ImportSheetsModalProps) {
  const handleAnalyze = async () => {
    if (!importState.url.trim()) {
      setImportState((prev: any) => ({ ...prev, error: "Please enter a Google Sheets URL" }));
      return;
    }
    if (!/^https:\/\/docs\.google\.com\/spreadsheets\/d\/[A-Za-z0-9_-]+/.test(importState.url)) {
      setImportState((prev: any) => ({ ...prev, error: "Invalid Google Sheets URL" }));
      return;
    }

    setImportState((prev: any) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await api.importSheetsAnalyze(importState.url);
      if (result && result.spreadsheet_title) {
        setImportState((prev: any) => ({
          ...prev,
          loading: false,
          spreadsheetId: result.spreadsheet_id,
          spreadsheetTitle: result.spreadsheet_title,
          sheetName: result.sheet_name,
          autoDetected: result.auto_detected,
          headers: result.headers,
          columnMapping: {
            name: result.column_mapping.find((c: any) => c.k === "name")?.v ?? null,
            registration_number: result.column_mapping.find((c: any) => c.k === "registration_number")?.v ?? null,
            email: result.column_mapping.find((c: any) => c.k === "email")?.v ?? null,
          },
          preview: result.preview,
          summary: result.summary,
        }));
      } else {
        setImportState((prev: any) => ({ ...prev, loading: false, error: "Analysis failed" }));
      }
    } catch (err: any) {
      setImportState((prev: any) => ({ ...prev, loading: false, error: err.message || "Analysis failed" }));
    }
  };

  const handleConfirm = async () => {
    if (!importState.columnMapping.name || !importState.columnMapping.registration_number || !importState.columnMapping.email) {
      setImportState((prev: any) => ({ ...prev, error: "Please map all three columns (Name, Registration Number, Email)" }));
      return;
    }

    const body = {
      spreadsheet_id: importState.spreadsheet_id,
      sheet_name: importState.sheetName,
      column_mapping: importState.columnMapping,
      headers: importState.headers,
      rows: importState.preview.map((p: any) => ({
        row: p.row,
        name: p.name,
        registration_number: p.registration_number,
        email: p.email,
        status: p.status,
        valid: p.valid,
      })),
    };

    setImportState((prev: any) => ({ ...prev, importLoading: true, error: null, result: null }));
    try {
      const result = await api.importSheetsConfirm(body);
      if (result.imported !== undefined) {
        setImportState((prev: any) => ({ ...prev, importLoading: false, result }));
      } else {
        setImportState((prev: any) => ({ ...prev, importLoading: false, error: "Import failed" }));
      }
    } catch (err: any) {
      setImportState((prev: any) => ({ ...prev, importLoading: false, error: err.message || "Import failed" }));
    }
  };

  return (
    <Modal open={show} onClose={onClose} title="Import Students from Google Sheets">
      <div className="space-y-4">
        {importState.loading && importState.result === null ? (
          <div className="text-sm text-[var(--text-muted)]">Analyzing spreadsheet...</div>
        ) : importState.result === null ? (
          <>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Google Sheets URL</label>
                <input
                  className="input-base"
                  value={importState.url}
                  onChange={(e) =>
                    setImportState((prev: any) => ({ ...prev, url: e.target.value }))
                  }
                  placeholder="https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Spreadsheet</label>
                <input
                  className="input-base"
                  value={importState.spreadsheetTitle}
                  disabled={importState.autoDetected}
                  readOnly
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Sheet</label>
                <input
                  className="input-base"
                  value={importState.sheetName}
                  disabled={importState.autoDetected}
                  readOnly
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Auto-detected columns</label>
                {importState.autoDetected && (
                  <span className="px-2 py-1 text-xs font-medium bg-[var(--primary-1)] text-[var(--primary-0)] rounded">
                    Name, Registration Number, Email
                  </span>
                )}
              </div>
            </div>

            {!importState.autoDetected && importState.headers.length > 0 && (
              <div className="mt-4">
                <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]">Manual column mapping</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div>
                    <label className="text-xs font-medium text-[var(--text-muted)]">Name</label>
                    <select
                      className="input-base w-full"
                      onChange={(e) =>
                        setImportState((prev: any) =>
                          {
                            const mapping = { ...prev.columnMapping };
                            mapping.name = e.target.value || null;
                            return { ...prev, columnMapping: mapping };
                          }
                        )}
                    >
                      <option value="">Select column</option>
                      {importState.headers.map((h: string, i: number) => (
                        <option key={i} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[var(--text-muted)]">Registration Number</label>
                    <select
                      className="input-base w-full"
                      onChange={(e) =>
                        setImportState((prev: any) =>
                          {
                            const mapping = { ...prev.columnMapping };
                            mapping.registration_number = e.target.value || null;
                            return { ...prev, columnMapping: mapping };
                          }
                        )}
                    >
                      <option value="">Select column</option>
                      {importState.headers.map((h: string, i: number) => (
                        <option key={i} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[var(--text-muted)]">Email</label>
                    <select
                      className="input-base w-full"
                      onChange={(e) =>
                        setImportState((prev: any) =>
                          {
                            const mapping = { ...prev.columnMapping };
                            mapping.email = e.target.value || null;
                            return { ...prev, columnMapping: mapping };
                          }
                        )}
                    >
                      <option value="">Select column</option>
                      {importState.headers.map((h: string, i: number) => (
                        <option key={i} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                {importState.columnMapping.name && importState.columnMapping.registration_number && importState.columnMapping.email && (
                  <p className="mt-2 text-sm text-[var(--primary-600)]">
                    Mapping: Name → {importState.columnMapping.name}, Registration → {importState.columnMapping.registration_number}, Email → {importState.columnMapping.email}
                  </p>
                )}
              </div>
            )}

            {importState.headers.length > 0 && importState.preview.length > 0 && (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)]">
                      <th className="p-2 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)]">#</th>
                      <th className="p-2 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)]">Name</th>
                      <th className="p-2 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)]">Registration Number</th>
                      <th className="p-2 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)]">Email</th>
                      <th className="p-2 text-left text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)]">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {importState.preview.map((p: any) => (
                      <tr key={p.row} className={p.valid ? "" : "bg-[rgba(251,113,133,0.1)]"}>
                        <td className="p-2 text-left text-xs font-mono">{p.row}</td>
                        <td className="p-2 text-left">{p.name || "-"}</td>
                        <td className="p-2 text-left text-xs font-mono">{p.registration_number || "-"}</td>
                        <td className="p-2 text-left text-xs">{p.email || "-"}</td>
                        <td className="p-2 text-left">
                          <Badge variant={p.valid ? "success" : "danger"}>
                            {p.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-2 text-sm">
                  {importState.summary.ready} Ready · {importState.summary.duplicates} Duplicate · {importState.summary.invalid} Invalid
                </p>
              </div>
            )}

            {importState.preview.length > 0 && !importState.importLoading && (
              <div className="mt-4">
                <Button
                  onClick={handleConfirm}
                  disabled={importState.importLoading}
                  variant="primary"
                  className="w-full"
                >
                  {importState.importLoading ? "Importing..." : "Import Students"}
                </Button>
              </div>
            )}

            {importState.error && (
              <div className="mt-3 p-3 rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] text-sm text-[var(--danger)]">
                {importState.error}
              </div>
            )}
          </>
        ) : (
          <div className="mt-4 p-4 rounded-xl bg-[var(--primary-50)] border border-[var(--primary-200)]">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-medium">Import Complete</p>
                <p className="text-[var(--text-muted)] small">
                  {importState.result.imported} students imported, {importState.result.skipped_duplicates} skipped (duplicates), {importState.result.invalid} invalid rows
                </p>
              </div>
              <button
                onClick={() => setImportState((prev: any) => ({ ...prev, result: null }))}
                className="text-[var(--primary)] text-sm font-medium hover:underline"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}