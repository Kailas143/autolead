"use client";

import React, { useState } from "react";
import { Upload, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

interface CSVUploaderProps {
  onUploadSuccess?: () => void;
}

export default function CSVUploader({ onUploadSuccess }: CSVUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [sheetUrl, setSheetUrl] = useState("");
  const [validateWhatsApp, setValidateWhatsApp] = useState(false);
  const [instanceName, setInstanceName] = useState("supermarket_campaign");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [source, setSource] = useState<"apollo" | "google">("apollo");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus("idle");
      setErrorMessage("");
    }
  };

  const handleUpload = async () => {
    if (source === "apollo" && !file) return;
    if (source === "google" && !sheetUrl.trim()) return;
    if (validateWhatsApp && !instanceName.trim()) return;

    setUploading(true);
    setStatus("idle");
    setProgress(0);
    setErrorMessage("");

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval);
          return 95;
        }
        return prev + 5;
      });
    }, 100);

    // Actual upload logic
    try {
      const formData = new FormData();
      formData.append("source", source);
      formData.append("validate_whatsapp", String(validateWhatsApp));
      if (validateWhatsApp) {
        formData.append("instance_name", instanceName.trim());
      }
      if (source === "apollo") {
        formData.append("file", file as File);
      } else {
        formData.append("sheet_url", sheetUrl.trim());
      }

      await api.post("/leads/upload", formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || progressEvent.loaded)
          );
          setProgress(percentCompleted);
        },
      });

      clearInterval(interval);
      setProgress(100);
      setStatus("success");
      setErrorMessage("");

      // Notify parent to refresh list if needed
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const err = error as any;
      const detail = err?.response?.data?.detail;
      console.error("Upload failed:", err);
      if (detail) {
        console.error("Upload error detail:", detail);
        const normalizedDetail = String(detail).toLowerCase();
        if (
          source === "google" &&
          (normalizedDetail.includes("not publicly accessible") ||
            normalizedDetail.includes("400") ||
            normalizedDetail.includes("failed to fetch google sheet") ||
            normalizedDetail.includes("published as csv"))
        ) {
          setErrorMessage(
            "Could not access this Google Sheet. Please use the normal docs.google.com sheet URL and make sure the sheet is public or published as CSV."
          );
        } else {
          setErrorMessage(String(detail));
        }
      } else {
        setErrorMessage(
          source === "google"
            ? "Failed to import leads from Google Sheets. Please check the sheet URL and confirm the sheet is public or published as CSV."
            : "Failed to import leads. Please check the CSV format and try again."
        );
      }
      clearInterval(interval);
      setStatus("error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-center gap-6 mb-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="source"
            value="apollo"
            checked={source === "apollo"}
            onChange={() => {
              setSource("apollo");
              setSheetUrl("");
              setErrorMessage("");
              setStatus("idle");
            }}
            className="w-4 h-4 text-primary accent-primary"
            disabled={uploading}
          />
          <span className="text-sm font-medium">Apollo</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="source"
            value="google"
            checked={source === "google"}
            onChange={() => {
              setSource("google");
              setFile(null);
              setErrorMessage("");
              setStatus("idle");
            }}
            className="w-4 h-4 text-primary accent-primary"
            disabled={uploading}
          />
          <span className="text-sm font-medium">Google</span>
        </label>
      </div>

      <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={validateWhatsApp}
            onChange={(e) => setValidateWhatsApp(e.target.checked)}
            className="h-4 w-4 rounded border-white/20 bg-transparent accent-primary"
            disabled={uploading}
          />
          <span className="text-sm font-medium">Validate WhatsApp numbers during import</span>
        </label>

        {validateWhatsApp ? (
          <div className="space-y-2">
            <label htmlFor="csv-instance-name" className="text-sm font-medium text-foreground">
              Evolution Instance Name
            </label>
            <input
              id="csv-instance-name"
              type="text"
              value={instanceName}
              onChange={(e) => setInstanceName(e.target.value)}
              disabled={uploading}
              placeholder="e.g. supermarket_campaign"
              className="w-full rounded-xl border border-border px-4 py-3 text-sm focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
        ) : null}
      </div>

      <div
        className={cn(
          "border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center transition-all duration-300",
          source === "apollo" && file ? "border-primary/50 bg-primary/5" : "border-border hover:border-primary/30"
        )}
      >
        {source === "apollo" ? (
          <>
            <input
              type="file"
              id="csv-upload"
              className="hidden"
              accept=".csv"
              onChange={handleFileChange}
              disabled={uploading}
            />
            {file ? (
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                  <Upload className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">{file.name}</h3>
                <p className="text-sm text-muted-foreground mb-6">
                  {(file.size / 1024).toFixed(2)} KB
                </p>

                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setFile(null)} disabled={uploading}>
                    <X className="w-4 h-4 mr-2" /> Cancel
                  </Button>
                  <Button onClick={handleUpload} disabled={uploading}>
                    {uploading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Uploading...
                      </>
                    ) : (
                      "Start Import"
                    )}
                  </Button>
                </div>
              </div>
            ) : (
              <label
                htmlFor="csv-upload"
                className="flex flex-col items-center cursor-pointer"
              >
                <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">
                  <Upload className="w-8 h-8 text-muted-foreground group-hover:text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">Click to upload CSV</h3>
                <p className="text-sm text-muted-foreground">Support Apollo CSV exports only</p>
              </label>
            )}
          </>
        ) : (
          <div className="w-full max-w-2xl space-y-4">
            <div className="w-full space-y-2">
              <label htmlFor="sheet-url" className="text-sm font-medium text-foreground">
                Google Sheet URL
              </label>
              <input
                id="sheet-url"
                type="text"
                value={sheetUrl}
                onChange={(e) => {
                  setSheetUrl(e.target.value);
                  setStatus("idle");
                  setErrorMessage("");
                }}
                disabled={uploading}
                placeholder="Paste your Google Sheet link here"
                className="w-full rounded-xl border border-border px-4 py-3 text-sm focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
              <p className="text-sm text-muted-foreground">
                Use a standard Google Sheet URL and make sure the sheet is public or published as CSV. Include headers like Name, Type, Location, Email Address, Industry.
              </p>
            </div>

            <div className="flex items-center justify-center">
              <Button onClick={handleUpload} disabled={uploading || !sheetUrl.trim()}>
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Importing...
                  </>
                ) : (
                  "Start Import"
                )}
              </Button>
            </div>
          </div>
        )}
      </div>

      {uploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Importing leads...</span>
            <span className="font-medium text-foreground">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      )}

      {status === "success" && (
        <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-500">
          <CheckCircle2 className="w-5 h-5" />
          <p className="text-sm font-medium">CSV upload started! Leads will appear shortly.</p>
        </div>
      )}

      {status === "error" && (
        <div className="flex items-center gap-3 p-4 bg-destructive/10 border border-destructive/20 rounded-xl text-destructive">
          <AlertCircle className="w-5 h-5" />
          <p className="text-sm font-medium">
            {errorMessage || "Failed to import leads. Please check the file or sheet settings and try again."}
          </p>
        </div>
      )}
    </div>
  );
}
