import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
          <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
            <h1 className="text-xl font-bold text-red-600 mb-4">Что-то пошло не так</h1>
            <p className="text-slate-600 mb-4">
              При загрузке приложения произошла ошибка. Попробуйте обновить страницу.
            </p>
            {this.state.error && (
              <pre className="text-xs bg-slate-100 p-3 rounded-lg overflow-auto text-slate-700">
                {this.state.error.toString()}
              </pre>
            )}
            <button
              onClick={() => window.location.reload()}
              className="mt-4 w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700"
            >
              Обновить страницу
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
