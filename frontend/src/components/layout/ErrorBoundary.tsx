import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
          <div className="text-red-400 text-sm font-mono uppercase tracking-wider">
            Something went wrong
          </div>
          <pre className="text-xs text-gray-500 max-w-md text-center font-mono">
            {this.state.error?.message}
          </pre>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-3 py-1.5 text-xs border border-gray-700 rounded text-gray-400 hover:text-gray-200 hover:border-gray-600 transition-colors font-mono uppercase tracking-wider"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
