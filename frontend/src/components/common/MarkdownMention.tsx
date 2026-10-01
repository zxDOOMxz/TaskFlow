import { MentionRenderer } from './MentionRenderer'

interface MarkdownMentionProps {
  text: string
  workspaceSlug: string
}

export function MarkdownMention({ text, workspaceSlug }: MarkdownMentionProps) {
  if (!text) return <p className="text-slate-500 italic">Нет содержимого</p>

  const lines = text.split('\n')

  return (
    <div className="prose prose-slate max-w-none">
      {lines.map((line, index) => {
        if (!line.trim()) return <br key={index} />

        // Bold: **text**
        const parts: { type: 'text' | 'bold'; value: string; key: string }[] = []
        const boldRegex = /\*\*([^*]+)\*\*/g
        let lastIndex = 0
        let match
        while ((match = boldRegex.exec(line)) !== null) {
          if (match.index > lastIndex) {
            parts.push({ type: 'text', value: line.slice(lastIndex, match.index), key: `text-${lastIndex}` })
          }
          parts.push({ type: 'bold', value: match[1], key: `bold-${match.index}` })
          lastIndex = match.index + match[0].length
        }
        if (lastIndex < line.length) {
          parts.push({ type: 'text', value: line.slice(lastIndex), key: `text-${lastIndex}` })
        }

        return (
          <p key={index} className="mb-2">
            {parts.map((part) =>
              part.type === 'bold' ? (
                <strong key={part.key}>{part.value}</strong>
              ) : (
                <MentionRenderer key={part.key} text={part.value} workspaceSlug={workspaceSlug} />
              )
            )}
          </p>
        )
      })}
    </div>
  )
}
