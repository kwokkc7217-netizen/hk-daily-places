import { useState } from 'react'
import { runSql } from '../api.js'

const PRESETS = [
  { label: 'places 頭 10 筆', sql: 'SELECT * FROM places ORDER BY id DESC LIMIT 10' },
  { label: '文章總數', sql: 'SELECT status, COUNT(*) AS n FROM places GROUP BY status' },
  {
    label: '管理員列表',
    sql: 'SELECT id, username, role, created_at FROM admin_users',
  },
]

function isReadOnly(sql) {
  return /^\s*(select|with)\b/i.test(sql)
}

export default function Sql() {
  const [sql, setSql] = useState(PRESETS[0].sql)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function doRun() {
    const trimmed = sql.trim()
    if (!trimmed) {
      setError('請先輸入 SQL')
      return
    }
    if (!isReadOnly(trimmed)) {
      if (!window.confirm('呢句會改動資料庫，真係執行？')) return
    }
    setRunning(true)
    setError('')
    setResult(null)
    try {
      setResult(await runSql(trimmed))
    } catch (e) {
      setError('執行失敗：' + ((e.data && e.data.error) || e.message))
    }
    setRunning(false)
  }

  return (
    <div>
      <h2>數據庫</h2>
      <p
        style={{
          background: '#fff3cd',
          border: '1px solid #e6c200',
          borderRadius: 8,
          padding: '10px 14px',
        }}
      >
        ⚠️ 直接執行 SQL：呢度打嘅每一句都會即時喺 production DB 執行，冇 undo。唔熟就唔好亂㩒。
      </p>

      <div style={{ margin: '12px 0', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {PRESETS.map((p) => (
          <button key={p.label} type="button" onClick={() => setSql(p.sql)}>
            {p.label}
          </button>
        ))}
      </div>

      <div className="form">
        <label>
          SQL（一次一句，SELECT 最多回 500 列）
          <textarea
            rows={6}
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            style={{ fontFamily: 'monospace' }}
          />
        </label>
        <button type="button" onClick={doRun} disabled={running}>
          {running ? '執行中…' : '執行'}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && result.type === 'select' && (
        <section>
          <p className="msg">共 {result.rowCount} 列（最多 500）</p>
          {result.columns.length > 0 ? (
            <table className="tbl">
              <thead>
                <tr>
                  {result.columns.map((c) => (
                    <th key={c}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((r, i) => (
                  <tr key={i}>
                    {result.columns.map((c) => (
                      <td key={c}>{String(r[c] ?? '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>冇結果。</p>
          )}
        </section>
      )}

      {result && result.type === 'update' && (
        <p className="msg">影響 {result.updated} 列。</p>
      )}
    </div>
  )
}
