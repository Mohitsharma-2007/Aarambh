import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github-dark.css'

interface ReportViewerProps {
  content: string
  className?: string
}

export default function ReportViewer({ content, className }: ReportViewerProps) {
  return (
    <div className={`report-viewer ${className || ''}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-xl font-semibold text-text-primary mb-4 mt-6 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold text-text-primary mb-3 mt-5">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-text-primary mb-2 mt-4">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="text-sm text-text-secondary mb-3 leading-relaxed">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-inside text-sm text-text-secondary mb-3 space-y-1">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside text-sm text-text-secondary mb-3 space-y-1">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-sm text-text-secondary">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="text-text-primary font-semibold">{children}</strong>
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className
            return isInline ? (
              <code className="px-1.5 py-0.5 bg-bg-tertiary rounded text-xs font-data text-accent" {...props}>
                {children}
              </code>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            )
          },
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-accent/50 pl-4 my-3 text-text-muted italic">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>

      <style>{`
        .report-viewer {
          font-family: 'Geist', sans-serif;
          line-height: 1.6;
        }
        .report-viewer pre {
          background: var(--bg-tertiary);
          border: 1px solid var(--border-subtle);
          border-radius: 6px;
          padding: 12px;
          overflow-x: auto;
          margin-bottom: 16px;
        }
        .report-viewer pre code {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 12px;
        }
      `}</style>
    </div>
  )
}
