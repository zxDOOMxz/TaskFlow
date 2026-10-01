import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { TopBar } from '@/components/layout/TopBar'
import { FileUploader } from '@/components/files/FileUploader'
import { filesApi, UploadedFile } from '@/api/files'

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / k ** i).toFixed(1))} ${sizes[i]}`
}

export function FilesPage() {
  const { workspaceSlug } = useParams()
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    if (!workspaceSlug) return
    loadFiles()
  }, [workspaceSlug])

  const loadFiles = () => {
    filesApi.list(workspaceSlug!).then((res) => setFiles(res.data))
  }

  const handleUpload = async (file: File) => {
    if (!workspaceSlug) return
    setUploading(true)
    try {
      await filesApi.upload(workspaceSlug, file)
      loadFiles()
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (fileId: string) => {
    if (!workspaceSlug) return
    await filesApi.delete(workspaceSlug, fileId)
    loadFiles()
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar title="Файлы" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <FileUploader onUpload={handleUpload} />
          {uploading && <p className="text-sm text-slate-500">Загрузка...</p>}

          <div className="card divide-y divide-slate-200">
            {files.length === 0 ? (
              <p className="p-6 text-center text-slate-500">Нет загруженных файлов</p>
            ) : (
              files.map((file) => (
                <div key={file.id} className="p-4 flex items-center justify-between hover:bg-slate-50">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900 truncate">{file.original_name}</p>
                    <p className="text-sm text-slate-500">
                      {formatBytes(file.size_bytes)} • {file.uploaded_by.first_name} {file.uploaded_by.last_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    {file.url && (
                      <a
                        href={file.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        Скачать
                      </a>
                    )}
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(file.id)}
                    >
                      Удалить
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
