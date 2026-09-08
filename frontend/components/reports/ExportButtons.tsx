"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import { api, ApiError } from "@/lib/api";

interface ExportButtonsProps {
  classId?: string;
  fromDate?: string;
  toDate?: string;
}

export default function ExportButtons({ classId, fromDate, toDate }: ExportButtonsProps) {
  const [busy, setBusy] = useState<"csv" | "excel" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const params = {
    class_id: classId || undefined,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  };

  const run = async (type: "csv" | "excel") => {
    setBusy(type);
    setError(null);
    try {
      if (type === "csv") {
        await api.exportCSV(params);
      } else {
        await api.exportExcel(params);
      }
    } catch (e) {
      const err = e as ApiError;
      setError(err.message || "Export failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <Button variant="ghost" size="sm" onClick={() => run("csv")} disabled={busy !== null}>
          <Icon name="download" size={16} /> {busy === "csv" ? "Exporting..." : "Export CSV"}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => run("excel")} disabled={busy !== null}>
          <Icon name="download" size={16} /> {busy === "excel" ? "Exporting..." : "Export Excel"}
        </Button>
      </div>
      {error && <p className="text-xs text-[var(--danger)]">{error}</p>}
    </div>
  );
}
