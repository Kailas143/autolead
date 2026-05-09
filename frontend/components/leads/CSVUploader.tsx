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
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus("idle");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setStatus("idle");
    setProgress(0);

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
      formData.append("file", file);
      
      await api.post("/leads/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
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
      
      // Notify parent to refresh list if needed
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error) {
      console.error("Upload failed:", error);
      clearInterval(interval);
      setStatus("error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div
        className={cn(
          "border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center transition-all duration-300",
          file ? "border-primary/50 bg-primary/5" : "border-border hover:border-primary/30"
        )}
      >
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
            <p className="text-sm text-muted-foreground">
              Support Apollo CSV exports only
            </p>
          </label>
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
          <p className="text-sm font-medium">Failed to import leads. Please check CSV format.</p>
        </div>
      )}
    </div>
  );
}
