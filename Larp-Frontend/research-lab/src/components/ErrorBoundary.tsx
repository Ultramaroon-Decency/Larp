import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught React ErrorBoundary error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#F7F9FB] flex items-center justify-center p-6 text-[#191C1E] font-sans">
          <div className="max-w-md w-full bg-white border border-[#C6C6CD] rounded-lg shadow-lg p-6 flex flex-col items-center text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-[28px]">warning</span>
            </div>
            
            <div className="space-y-1">
              <h2 className="text-[20px] font-bold text-[#0F172A] tracking-tight">
                Something went wrong
              </h2>
              <p className="text-[14px] text-[#45464D]">
                An unexpected error occurred while rendering the application view.
              </p>
            </div>

            {this.state.error?.message && (
              <div className="w-full bg-[#F2F4F6] border border-[#E0E3E5] rounded p-3 text-left overflow-x-auto max-h-32">
                <code className="text-[12px] text-red-600 font-mono leading-relaxed block">
                  {this.state.error.message}
                </code>
              </div>
            )}

            <div className="flex items-center gap-3 w-full pt-2">
              <button
                type="button"
                onClick={this.handleReset}
                className="flex-1 py-2.5 px-4 rounded-md border border-[#C6C6CD] text-[13px] font-bold text-[#0F172A] hover:bg-[#E0E3E5] transition-colors cursor-pointer"
              >
                Try Again
              </button>
              <button
                type="button"
                onClick={this.handleReload}
                className="flex-1 py-2.5 px-4 rounded-md bg-[#0F172A] text-white text-[13px] font-bold hover:bg-slate-800 transition-colors shadow-xs cursor-pointer"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
