"use client"

import React, {RefObject, useCallback, useState} from "react"
import {AlertCircle, CheckCircle, Loader2, Upload, X} from "lucide-react"
import {Button} from "@/components/ui/button"
import {Progress} from "@/components/ui/progress"
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "@/components/ui/card"
import {excelToJson} from "@/app/functions";

interface FileStatus {
  name: string
  size: number
  progress: number
  status: "uploading" | "completed" | "error"
}

export default function FileUpload({setWarehouseAction}: {
  setWarehouseAction: (warehouse: boolean[][]) => void
}) {
  const [files, setFiles] = useState<FileStatus[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const simulateUpload = (file: File) => {
    const newFile: FileStatus = {
      name: file.name,
      size: file.size,
      progress: 0,
      status: "uploading",
    }

    setFiles((prev) => [...prev, newFile])

    const index = files.length

    const interval = setInterval(() => {
      setFiles((prev) => {
        const newFiles = [...prev]
        if (newFiles[index]) {
          if (newFiles[index].progress >= 100) {
            clearInterval(interval)
            newFiles[index].status = "completed"
            excelToJson(file).then((result: Array<Record<string, number>>) => {
              let maxWidth = 0
              let maxHeight = 0
              result.forEach((pair: Record<string, number>) => {
                maxHeight = Math.max(maxHeight, pair.x)
                maxWidth = Math.max(maxWidth, pair.y)
              })
              let warehouse: boolean[][] = Array.from({length: maxHeight}, () => Array(maxWidth).fill(false))
              result.forEach((pair: Record<string, number>) => {
                warehouse[pair.x - 1][pair.y - 1] = true
              })
              warehouse = warehouse.reverse()
              warehouse.forEach((row) => row.reverse())
              setWarehouseAction(warehouse)
            })
          } else {
            newFiles[index].progress += 5
          }
        }
        return newFiles
      })
    }, 100)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    droppedFiles.forEach(simulateUpload)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      selectedFiles.forEach(simulateUpload)
    }
  }, [])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <Card className="mx-auto">
      <CardHeader>
        <CardTitle>Загрузка файла</CardTitle>
        <CardDescription>Перетащите файл сюда или нажмите, чтобы выбрать файл</CardDescription>
      </CardHeader>
      <CardContent>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
            isDragging ? "border-primary bg-primary/5" : "border-gray-300 hover:border-primary"
          }`}
        >
          <input
            type="file"
            multiple
            onChange={handleFileSelect}
            className="absolute inset-0 cursor-pointer opacity-0"
          />
          <Upload className="mb-4 h-10 w-10 text-gray-400"/>
          <p className="text-sm text-gray-600 dark:text-gray-400">Перетащите сюда файл или нажмите для выбора</p>
        </div>

        {files.length > 0 && (
          <div className="mt-6 space-y-4">
            {files.map((file, index) => (
              <div key={index} className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center space-x-4">
                  {file.status === "uploading" ? (
                    <Loader2 className="h-5 w-5 animate-spin text-primary"/>
                  ) : file.status === "completed" ? (
                    <CheckCircle className="h-5 w-5 text-green-500"/>
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500"/>
                  )}
                  <div>
                    <p className="text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <div className="flex w-32 items-center space-x-2">
                  <Progress value={file.progress} className="h-2"/>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => {
                      setFiles((prev) => prev.filter((_, i) => i !== index))
                      setWarehouseAction([])
                    }}
                  >
                    <X className="h-4 w-4"/>
                    <span className="sr-only">Удалить файл</span>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

