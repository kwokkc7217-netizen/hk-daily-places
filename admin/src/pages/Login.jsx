import { useState } from 'react'
import { login } from '../api.js'

export default function Login({ onDone }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(username, password)
      onDone()
    } catch (err) {
      setError(err.status === 401 ? '帳號或密碼錯誤' : '登入失敗，請稍後再試')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="wrap narrow">
      <h1>CMS 登入</h1>
      <form onSubmit={submit} className="form">
        <label>
          帳號
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        </label>
        <label>
          密碼
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? '登入中…' : '登入'}
        </button>
      </form>
    </div>
  )
}
