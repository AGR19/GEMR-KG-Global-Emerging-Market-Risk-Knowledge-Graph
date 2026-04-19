import React, { useState, useRef, useEffect } from 'react';

const EXAMPLE_QUESTIONS = [
  "What was China's GDP in 2020?",
  "Show the CPI trend for Brazil from 2010 to 2020",
  "Which country had the highest risk score in 2023?",
  "Compare political stability of Thailand and Mexico",
  "What are Poland's governance and economic health scores?",
  "Show all indicators for Philippines in 2015",
];

const AskAI = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check backend health on mount
  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(data => setBackendStatus(data))
      .catch(() => setBackendStatus({ status: 'error' }));
  }, []);

  const handleSend = async (question) => {
    const q = (question || input).trim();
    if (!q || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setLoading(true);

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, use_history: true }),
      });
      const data = await res.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: {
          success: false,
          error: 'Could not reach the backend. Is the FastAPI server running?',
          sparql: '',
          question: q,
        },
      }]);
    }

    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.headerIcon}>🤖</span>
          <div>
            <h2 style={styles.headerTitle}>Ask GEMR-KG</h2>
            <p style={styles.headerSub}>Natural language queries powered by ontology-aware AI</p>
          </div>
        </div>
        <div style={{
          ...styles.statusDot,
          background: backendStatus?.status === 'ok' ? '#22c55e' : '#ef4444',
        }}>
          {backendStatus?.status === 'ok' ? '● Online' : '● Offline'}
        </div>
      </div>

      {/* Messages Area */}
      <div style={styles.messagesArea}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>💬</div>
            <h3 style={styles.emptyTitle}>Ask a question about emerging market risk</h3>
            <p style={styles.emptyDesc}>
              Your question will be translated into a SPARQL query, executed against the knowledge graph,
              and automatically repaired if needed.
            </p>
            <div style={styles.chipContainer}>
              {EXAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  style={styles.chip}
                  onClick={() => handleSend(q)}
                  onMouseOver={e => {
                    e.currentTarget.style.background = '#3b82f6';
                    e.currentTarget.style.color = '#fff';
                    e.currentTarget.style.borderColor = '#3b82f6';
                  }}
                  onMouseOut={e => {
                    e.currentTarget.style.background = 'rgba(59,130,246,0.08)';
                    e.currentTarget.style.color = '#3b82f6';
                    e.currentTarget.style.borderColor = 'rgba(59,130,246,0.25)';
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} style={{
            ...styles.messageRow,
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            {msg.role === 'user' ? (
              <UserMessage content={msg.content} />
            ) : (
              <AssistantMessage data={msg.content} />
            )}
          </div>
        ))}

        {loading && (
          <div style={styles.messageRow}>
            <div style={styles.thinkingBubble}>
              <div style={styles.thinkingDots}>
                <span style={{ ...styles.dot, animationDelay: '0s' }}>●</span>
                <span style={{ ...styles.dot, animationDelay: '0.2s' }}>●</span>
                <span style={{ ...styles.dot, animationDelay: '0.4s' }}>●</span>
              </div>
              <span style={styles.thinkingText}>Generating SPARQL & querying knowledge graph...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={styles.inputArea}>
        <div style={styles.inputWrapper}>
          <textarea
            id="ask-ai-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about emerging market risk data..."
            style={styles.textarea}
            rows={1}
            disabled={loading}
          />
          <button
            id="ask-ai-send"
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            style={{
              ...styles.sendBtn,
              opacity: !input.trim() || loading ? 0.4 : 1,
              cursor: !input.trim() || loading ? 'not-allowed' : 'pointer',
            }}
          >
            ↑
          </button>
        </div>
        <p style={styles.inputHint}>
          Press Enter to send · Shift+Enter for new line · Powered by Gemini 2.0 Flash
        </p>
      </div>
    </div>
  );
};


/* ─── Sub-Components ──────────────────────────────────────── */

const UserMessage = ({ content }) => (
  <div style={styles.userBubble}>
    {content}
  </div>
);

const AssistantMessage = ({ data }) => {
  const [showTable, setShowTable] = useState(false);
  const [showSparql, setShowSparql] = useState(false);
  const [showIris, setShowIris] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  if (!data) return null;

  const { success, sparql, results, attempts, grounded_iris, elapsed_seconds, error, history } = data;
  const bindings = results?.results?.bindings || [];
  const vars = results?.head?.vars || [];

  return (
    <div style={styles.assistantBubble}>
      {/* Status Badge */}
      <div style={styles.badgeRow}>
        <span style={{
          ...styles.badge,
          background: success ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
          color: success ? '#16a34a' : '#dc2626',
        }}>
          {success ? '✓ Query Succeeded' : '✗ Query Failed'}
        </span>
        {attempts > 1 && (
          <span style={{ ...styles.badge, background: 'rgba(234,179,8,0.12)', color: '#ca8a04' }}>
            🔄 Fixed in {attempts} attempts
          </span>
        )}
        {attempts === 1 && success && (
          <span style={{ ...styles.badge, background: 'rgba(59,130,246,0.12)', color: '#2563eb' }}>
            ⚡ 1st try
          </span>
        )}
        <span style={{ ...styles.badge, background: 'rgba(107,114,128,0.08)', color: '#6b7280' }}>
          {elapsed_seconds}s
        </span>
      </div>

      {/* Natural Language Answer */}
      {data.nl_answer && (
        <div style={styles.nlAnswerBox}>
          {data.nl_answer}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={styles.errorBox}>
          {error}
        </div>
      )}

      {/* Collapsible: Results Table */}
      {success && bindings.length > 0 && (
        <div style={styles.collapsible}>
          <button
            style={styles.collapseBtn}
            onClick={() => setShowTable(!showTable)}
          >
            {showTable ? '▼' : '▶'} View Data Table ({bindings.length} rows)
          </button>
          {showTable && (
            <div style={{ ...styles.resultsSection, marginTop: '8px' }}>
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      {vars.map(v => (
                        <th key={v} style={styles.th}>?{v}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {bindings.slice(0, 50).map((binding, idx) => (
                      <tr key={idx} style={{ background: idx % 2 === 0 ? '#fafbfc' : '#fff' }}>
                        {vars.map(v => (
                          <td key={v} style={styles.td}>
                            {binding[v] ? formatValue(binding[v]) : '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {bindings.length > 50 && (
                  <p style={styles.truncated}>Showing 50 of {bindings.length} results</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {success && bindings.length === 0 && (
        <div style={styles.emptyResults}>
          No results found for this query. Try rephrasing your question.
        </div>
      )}

      {/* Collapsible: SPARQL Query */}
      {sparql && (
        <div style={styles.collapsible}>
          <button
            style={styles.collapseBtn}
            onClick={() => setShowSparql(!showSparql)}
          >
            {showSparql ? '▼' : '▶'} Generated SPARQL
          </button>
          {showSparql && (
            <pre style={styles.codeBlock}>{sparql}</pre>
          )}
        </div>
      )}

      {/* Collapsible: Grounded IRIs */}
      {grounded_iris && grounded_iris.length > 0 && (
        <div style={styles.collapsible}>
          <button
            style={styles.collapseBtn}
            onClick={() => setShowIris(!showIris)}
          >
            {showIris ? '▼' : '▶'} Grounded IRIs ({grounded_iris.length})
          </button>
          {showIris && (
            <div style={styles.iriList}>
              {grounded_iris.map((iri, i) => (
                <div key={i} style={styles.iriItem}>
                  <span style={styles.iriName}>{iri.label}</span>
                  <span style={styles.iriType}>{iri.type}</span>
                  <span style={styles.iriScore}>{iri.score}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Collapsible: Attempt History */}
      {history && history.length > 1 && (
        <div style={styles.collapsible}>
          <button
            style={styles.collapseBtn}
            onClick={() => setShowHistory(!showHistory)}
          >
            {showHistory ? '▼' : '▶'} Self-Healing Log ({history.length} attempts)
          </button>
          {showHistory && (
            <div style={styles.historyList}>
              {history.map((h, i) => (
                <div key={i} style={styles.historyItem}>
                  <span style={{
                    ...styles.historyBadge,
                    color: h.success ? '#16a34a' : '#dc2626',
                  }}>
                    Attempt {h.attempt}: {h.success ? '✓' : '✗'}
                  </span>
                  {h.error && (
                    <pre style={styles.historyError}>{h.error.slice(0, 200)}</pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};


/* ─── Helpers ─────────────────────────────────────────────── */

function formatValue(val) {
  if (!val) return '—';
  let v = val.value || '';
  // Shorten URIs
  if (v.startsWith('https://gemr-kg.org/ontology#')) {
    v = v.replace('https://gemr-kg.org/ontology#', 'gemr:');
  }
  // Format numbers
  if (val.datatype && val.datatype.includes('decimal') || val.datatype?.includes('float') || val.datatype?.includes('double')) {
    const num = parseFloat(v);
    if (!isNaN(num)) {
      return num.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
  }
  return v;
}


/* ─── Styles ──────────────────────────────────────────────── */

const pulseKeyframes = `
@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
`;

// Inject keyframes
if (typeof document !== 'undefined' && !document.getElementById('askai-keyframes')) {
  const style = document.createElement('style');
  style.id = 'askai-keyframes';
  style.textContent = pulseKeyframes;
  document.head.appendChild(style);
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    width: '100%',
    background: '#f8fafc',
    borderRadius: '12px',
    overflow: 'hidden',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  },

  // Header
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 24px',
    borderBottom: '1px solid #e2e8f0',
    background: '#fff',
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '12px' },
  headerIcon: { fontSize: '28px' },
  headerTitle: { margin: 0, fontSize: '18px', fontWeight: 700, color: '#0f172a' },
  headerSub: { margin: 0, fontSize: '13px', color: '#64748b' },
  statusDot: {
    fontSize: '12px',
    padding: '4px 10px',
    borderRadius: '20px',
    fontWeight: 600,
  },

  // Messages
  messagesArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  messageRow: {
    display: 'flex',
    width: '100%',
  },

  // User bubble
  userBubble: {
    maxWidth: '75%',
    padding: '12px 18px',
    borderRadius: '18px 18px 4px 18px',
    background: '#3b82f6',
    color: '#fff',
    fontSize: '14px',
    lineHeight: '1.5',
    fontWeight: 500,
  },

  // Assistant bubble
  assistantBubble: {
    maxWidth: '90%',
    width: '100%',
    padding: '18px',
    borderRadius: '4px 18px 18px 18px',
    background: '#fff',
    border: '1px solid #e2e8f0',
    fontSize: '14px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  },

  // Badges
  badgeRow: { display: 'flex', gap: '8px', flexWrap: 'wrap' },
  badge: {
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
  },

  // Error
  errorBox: {
    padding: '10px 14px',
    borderRadius: '8px',
    background: 'rgba(239,68,68,0.06)',
    border: '1px solid rgba(239,68,68,0.15)',
    color: '#b91c1c',
    fontSize: '13px',
    lineHeight: '1.5',
  },

  nlAnswerBox: {
    padding: '12px 16px',
    borderRadius: '8px',
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    color: '#0f172a',
    fontSize: '15px',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
  },

  // Results table
  resultsSection: {
    borderRadius: '8px',
    border: '1px solid #e2e8f0',
    overflow: 'hidden',
  },
  resultsHeader: {
    padding: '8px 14px',
    background: '#f1f5f9',
    borderBottom: '1px solid #e2e8f0',
  },
  resultsTitle: { fontSize: '13px', fontWeight: 600, color: '#475569' },
  tableWrapper: { overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: '13px' },
  th: {
    padding: '8px 12px',
    textAlign: 'left',
    background: '#f8fafc',
    borderBottom: '2px solid #e2e8f0',
    color: '#475569',
    fontWeight: 600,
    position: 'sticky',
    top: 0,
    fontSize: '12px',
  },
  td: {
    padding: '7px 12px',
    borderBottom: '1px solid #f1f5f9',
    color: '#334155',
    maxWidth: '250px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  truncated: { padding: '8px 14px', fontSize: '12px', color: '#94a3b8', margin: 0 },

  emptyResults: {
    padding: '16px',
    textAlign: 'center',
    color: '#94a3b8',
    fontStyle: 'italic',
    fontSize: '13px',
  },

  // Collapsibles
  collapsible: { borderTop: '1px solid #f1f5f9', paddingTop: '8px' },
  collapseBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '13px',
    color: '#64748b',
    fontWeight: 500,
    padding: '4px 0',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  codeBlock: {
    margin: '8px 0 0',
    padding: '14px',
    background: '#1e293b',
    color: '#e2e8f0',
    borderRadius: '8px',
    fontSize: '12px',
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    overflowX: 'auto',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
  },

  // Grounded IRIs
  iriList: { marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' },
  iriItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '4px 8px',
    borderRadius: '6px',
    background: '#f8fafc',
    fontSize: '12px',
  },
  iriName: { fontWeight: 600, color: '#334155', flex: 1 },
  iriType: { color: '#64748b', fontSize: '11px', background: '#e2e8f0', padding: '1px 6px', borderRadius: '4px' },
  iriScore: { color: '#94a3b8', fontSize: '11px', fontFamily: 'monospace' },

  // History
  historyList: { marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' },
  historyItem: { padding: '6px 8px', borderRadius: '6px', background: '#f8fafc' },
  historyBadge: { fontSize: '12px', fontWeight: 600 },
  historyError: {
    margin: '4px 0 0',
    padding: '6px 8px',
    background: '#fef2f2',
    borderRadius: '4px',
    fontSize: '11px',
    color: '#991b1b',
    whiteSpace: 'pre-wrap',
    overflowX: 'auto',
  },

  // Thinking animation
  thinkingBubble: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 18px',
    borderRadius: '4px 18px 18px 18px',
    background: '#fff',
    border: '1px solid #e2e8f0',
  },
  thinkingDots: { display: 'flex', gap: '4px' },
  dot: {
    fontSize: '14px',
    color: '#3b82f6',
    animation: 'pulse 1.2s infinite',
  },
  thinkingText: { fontSize: '13px', color: '#94a3b8' },

  // Empty state
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    textAlign: 'center',
    padding: '40px',
  },
  emptyIcon: { fontSize: '48px', marginBottom: '16px' },
  emptyTitle: { margin: '0 0 8px', fontSize: '18px', fontWeight: 600, color: '#0f172a' },
  emptyDesc: { margin: '0 0 24px', fontSize: '14px', color: '#64748b', maxWidth: '460px', lineHeight: '1.6' },
  chipContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    justifyContent: 'center',
    maxWidth: '560px',
  },
  chip: {
    padding: '8px 14px',
    borderRadius: '20px',
    border: '1px solid rgba(59,130,246,0.25)',
    background: 'rgba(59,130,246,0.08)',
    color: '#3b82f6',
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    fontWeight: 500,
  },

  // Input area
  inputArea: {
    padding: '16px 24px',
    borderTop: '1px solid #e2e8f0',
    background: '#fff',
  },
  inputWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 8px 8px 16px',
    border: '2px solid #e2e8f0',
    borderRadius: '14px',
    background: '#f8fafc',
    transition: 'border-color 0.2s',
  },
  textarea: {
    flex: 1,
    border: 'none',
    outline: 'none',
    background: 'transparent',
    fontSize: '14px',
    fontFamily: 'inherit',
    resize: 'none',
    lineHeight: '1.5',
    color: '#0f172a',
  },
  sendBtn: {
    width: '36px',
    height: '36px',
    borderRadius: '10px',
    border: 'none',
    background: '#3b82f6',
    color: '#fff',
    fontSize: '18px',
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'opacity 0.2s',
    flexShrink: 0,
  },
  inputHint: {
    margin: '8px 0 0',
    fontSize: '11px',
    color: '#94a3b8',
    textAlign: 'center',
  },
};

export default AskAI;
