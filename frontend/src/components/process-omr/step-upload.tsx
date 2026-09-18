import { useState, useRef, useCallback } from "react";
import { Upload, X, FileImage } from "lucide-react";
import { Button } from "../ui/button";

type Props = {
  files: File[];
  onFilesChange: (files: File[]) => void;
};

const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"];
const ACCEPTED_MIME_TYPES = [
  "image/jpeg",
  "image/png",
  "image/bmp",
  "image/tiff",
  "application/pdf",
];

export function StepUpload({ files, onFilesChange }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (newFiles: FileList | File[]) => {
      const arr = Array.from(newFiles);
      const valid = arr.filter((f) => {
        const ext = "." + f.name.split(".").pop()?.toLowerCase();
        return ACCEPTED_EXTENSIONS.includes(ext) || ACCEPTED_MIME_TYPES.includes(f.type);
      });
      if (valid.length > 0) {
        onFilesChange([...files, ...valid]);
      }
    },
    [files, onFilesChange]
  );

  const removeFile = useCallback(
    (index: number) => {
      onFilesChange(files.filter((_, i) => i !== index));
    },
    [files, onFilesChange]
  );

  const clearAll = useCallback(() => {
    onFilesChange([]);
  }, [onFilesChange]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files);
      }
    },
    [addFiles]
  );

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        addFiles(e.target.files);
        e.target.value = "";
      }
    },
    [addFiles]
  );

  const totalSize = files.reduce((sum, f) => sum + f.size, 0);
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
          isDragging
            ? "border-blue-400 bg-blue-50"
            : "border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100"
        }`}
      >
        <Upload className="mb-3 h-8 w-8 text-slate-400" />
        <p className="text-sm font-medium text-slate-700">
          Drag and drop OMR sheets here, or click to browse
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Supported: JPG, JPEG, PNG, BMP, TIFF, PDF — Named as STUDENTCODE.extension (e.g. 0607harshkhatri.jpg)
        </p>
        <p className="mt-1 text-xs text-slate-400">
          Code format: 2-digit school number + 2-digit class + student name (no spaces)
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-700">
              {files.length} file{files.length !== 1 ? "s" : ""} selected ({formatSize(totalSize)})
            </p>
            <Button variant="ghost" size="default" onClick={clearAll} className="h-8 text-xs text-red-600 hover:text-red-700">
              Clear all
            </Button>
          </div>

          <div className="max-h-64 overflow-y-auto rounded-lg border bg-white">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between border-b border-slate-100 px-3 py-2 last:border-b-0"
              >
                <div className="flex items-center gap-2">
                  <FileImage className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-700">{file.name}</span>
                  <span className="text-xs text-slate-400">{formatSize(file.size)}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
