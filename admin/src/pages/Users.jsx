import { useEffect, useState } from 'react'
import { listUsers, createUser, deleteUser, changeMyPassword } from '../api.js'

function friendly(e) {
  return (e.data && e.data.error) || 'HTTP ' + e.status
}

export default function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newName, setNewName] = useState('')
  const [newPass, setNewPass] = useState('')
  const [addMsg, setAddMsg] = useState('')
  const [pw1, setPw1] = useState('')
  const [pw2, setPw2] = useState('')
  const [pwMsg, setPwMsg] = useState('')

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      setUsers(await listUsers())
    } catch (e) {
      setError('讀取管理員列表失敗：' + friendly(e))
    }
    setLoading(false)
  }

  useEffect(() => {
    refresh()
  }, [])

  async function doAdd(ev) {
    ev.preventDefault()
    setAddMsg('')
    if (!newName.trim() || !newPass) {
      setAddMsg('請輸入帳號同密碼')
      return
    }
    if (newPass.length < 8) {
      setAddMsg('密碼最少 8 個字')
      return
    }
    try {
      await createUser(newName.trim(), newPass)
      setNewName('')
      setNewPass('')
      setAddMsg('已新增管理員')
      refresh()
    } catch (e) {
      setAddMsg('新增失敗：' + friendly(e))
    }
  }

  async function doDelete(id, username) {
    if (!window.confirm('真係要刪除管理員「' + username + '」？')) return
    setError('')
    try {
      await deleteUser(id)
      refresh()
    } catch (e) {
      setError('刪除失敗：' + friendly(e))
    }
  }

  async function doChangePw(ev) {
    ev.preventDefault()
    setPwMsg('')
    if (pw1.length < 8) {
      setPwMsg('新密碼最少 8 個字')
      return
    }
    if (pw1 !== pw2) {
      setPwMsg('兩次輸入嘅密碼唔一致')
      return
    }
    try {
      await changeMyPassword(pw1)
      setPw1('')
      setPw2('')
      setPwMsg('密碼已更新')
    } catch (e) {
      setPwMsg('更新失敗：' + friendly(e))
    }
  }

  function fmtDate(s) {
    return s ? s.replace('T', ' ').slice(0, 19) : ''
  }

  return (
    <div>
      <h2>管理員</h2>
      {error && <p className="error">{error}</p>}

      <section>
        <h3>管理員列表</h3>
        {loading ? (
          <p>載入中…</p>
        ) : (
          <table className="tbl">
            <thead>
              <tr>
                <th>帳號</th>
                <th>角色</th>
                <th>建立時間</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.role}</td>
                  <td>{fmtDate(u.createdAt)}</td>
                  <td className="actions">
                    <button className="danger" onClick={() => doDelete(u.id, u.username)}>
                      刪除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h3>新增管理員</h3>
        <form onSubmit={doAdd} className="form">
          <label>
            帳號
            <input value={newName} onChange={(e) => setNewName(e.target.value)} />
          </label>
          <label>
            密碼（最少 8 個字）
            <input type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} />
          </label>
          <button type="submit">新增</button>
        </form>
        {addMsg && <p className="msg">{addMsg}</p>}
      </section>

      <section>
        <h3>更改我的密碼</h3>
        <form onSubmit={doChangePw} className="form">
          <label>
            新密碼（最少 8 個字）
            <input type="password" value={pw1} onChange={(e) => setPw1(e.target.value)} />
          </label>
          <label>
            再入一次
            <input type="password" value={pw2} onChange={(e) => setPw2(e.target.value)} />
          </label>
          <button type="submit">更新密碼</button>
        </form>
        {pwMsg && <p className="msg">{pwMsg}</p>}
      </section>
    </div>
  )
}
