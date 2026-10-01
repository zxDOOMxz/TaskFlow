import { useRef, useState } from 'react'

interface FileUploaderProps {
  onUpload: (file: File) => void
  accept?: string
}

export function FileUploader({ onUpload, accept }: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onUpload(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onUpload(file)
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
        dragOver ? 'border-primary-500 bg-primary-50' : 'border-slate-300 hover:border-primary-400'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={accept}
        onChange={handleFileSelect}
      />
      <p className="text-sm text-slate-600">
        Перетащите файл сюда или нажмите для выбора
      </p>
    </div>
  )
}
