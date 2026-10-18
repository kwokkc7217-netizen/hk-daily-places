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

function isSingleReadOnly(sql) {
  const trimmed = sql.trim()
  return /^\s*(select|with)\b/i.test(trimmed) && !trimmed.includes(';')
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
    if (!isSingleReadOnly(trimmed)) {
      if (!window.confirm('呢句會改動資料庫，真係執行？')) return
    }
    setRunning(true)
    setError('')
    setResult(null)
    try {
      setResult(await runSql(trimmed))
    } catch (e) {
      const d = e.data || {}
      setError(
        d.failedAt != null && d.failedAt >= 0
          ? `第 ${d.failedAt + 1} 句出錯，成批已 rollback：${d.error || e.message}`
          : '執行失敗：' + (d.error || e.message)
      )
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
        <br />
        可以一次貼多句（例如成份 INSERT dump）：多句會包喺同一個 transaction，一句失敗就成批 rollback。
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
          SQL（可一次貼多句；每個 SELECT 最多回 500 列）
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

      {result && result.results && (
        <section>
          <p className="msg">
            共 {result.statements} 句，全部執行成功。
          </p>
          {result.results.map((r) => (
            <div key={r.index} style={{ marginBottom: 16 }}>
              <p className="msg">第 {r.index + 1} 句：</p>
              {r.type === 'select' && (
                <>
                  <p className="msg">共 {r.rowCount} 列（最多 500）</p>
                  {r.columns.length > 0 ? (
                    <table className="tbl">
                      <thead>
                        <tr>
                          {r.columns.map((c) => (
                            <th key={c}>{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {r.rows.map((row, i) => (
                          <tr key={i}>
                            {r.columns.map((c) => (
                              <td key={c}>{String(row[c] ?? '')}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p>冇結果。</p>
                  )}
                </>
              )}
              {r.type === 'update' && <p className="msg">影響 {r.updated} 列。</p>}
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
