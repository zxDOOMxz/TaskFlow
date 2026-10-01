import { Link } from 'react-router-dom'

interface MentionRendererProps {
  text: string
  workspaceSlug: string
}

export function MentionRenderer({ text, workspaceSlug }: MentionRendererProps) {
  if (!text) return null

  // Regex patterns
  const patterns = [
    { type: 'issue', regex: /#([A-Z][A-Z0-9]*-\d+)/g },
    { type: 'page', regex: /\[\[([^\]]+)\]\]/g },
    { type: 'user', regex: /@([a-zA-Z0-9_.-]+)/g },
  ]

  // Build tokens
  const tokens: { type: 'text' | 'issue' | 'page' | 'user'; value: string; key: string }[] = []
  let lastIndex = 0

  // Find all matches across all patterns
  const allMatches: { index: number; end: number; type: 'issue' | 'page' | 'user'; value: string }[] = []

  patterns.forEach(({ type, regex }) => {
    let match
    while ((match = regex.exec(text)) !== null) {
      allMatches.push({
        index: match.index,
        end: match.index + match[0].length,
        type: type as 'issue' | 'page' | 'user',
        value: match[1],
      })
    }
  })

  // Sort by index
  allMatches.sort((a, b) => a.index - b.index)

  // Merge non-overlapping matches
  const merged: typeof allMatches = []
  for (const match of allMatches) {
    if (merged.length === 0 || match.index >= merged[merged.length - 1].end) {
      merged.push(match)
    }
  }

  for (const match of merged) {
    if (match.index > lastIndex) {
      tokens.push({ type: 'text', value: text.slice(lastIndex, match.index), key: `text-${lastIndex}` })
    }
    tokens.push({ type: match.type, value: match.value, key: `${match.type}-${match.index}` })
    lastIndex = match.end
  }

  if (lastIndex < text.length) {
    tokens.push({ type: 'text', value: text.slice(lastIndex), key: `text-${lastIndex}` })
  }

  return (
    <>
      {tokens.map((token) => {
        if (token.type === 'text') {
          return <span key={token.key}>{token.value}</span>
        }

        if (token.type === 'issue') {
          return (
            <Link
              key={token.key}
              to={`/w/${workspaceSlug}/projects/${token.value.split('-')[0]}/issues/${token.value}`}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              #{token.value}
            </Link>
          )
        }

        if (token.type === 'page') {
          return (
            <Link
              key={token.key}
              to={`/w/${workspaceSlug}/wiki`}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              {token.value}
            </Link>
          )
        }

        if (token.type === 'user') {
          return (
            <span key={token.key} className="text-primary-600 font-medium">
              @{token.value}
            </span>
          )
        }

        return null
      })}
    </>
  )
}
