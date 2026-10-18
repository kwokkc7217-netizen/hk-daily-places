import { useEffect, useState } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import { me, logout } from './api.js'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Editor from './pages/Editor.jsx'
import Users from './pages/Users.jsx'

export default function App() {
  const [user, setUser] = useState(undefined) // undefined = 載入中

  useEffect(() => {
    me()
      .then((d) => setUser(d.username))
      .catch(() => setUser(null))
  }, [])

  async function doLogout() {
    try {
      await logout()
    } catch (e) {
      // 登出失敗都照 reload，session 多數已經冇咗
    }
    window.location.href = '/admin/'
  }

  if (user === undefined) {
    return (
      <div className="wrap">
        <p>載入中…</p>
      </div>
    )
  }

  if (user === null) {
    return <Login onDone={() => window.location.reload()} />
  }

  return (
    <div className="wrap">
      <header className="topbar">
        <strong>每日香港好去處 · CMS</strong>
        <nav>
          <Link to="/">文章管理</Link>
          <Link to="/new">新增文章</Link>
          <Link to="/users">管理員</Link>
          <button onClick={doLogout}>登出 ({user})</button>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<Editor />} />
        <Route path="/edit/:id" element={<Editor />} />
        <Route path="/users" element={<Users />} />
        <Route path="*" element={<Dashboard />} />
      </Routes>
    </div>
  )
}
