import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listPlaces, deletePlace, savePlace } from '../api.js'

const CAT = { HIKING: '行山', SHOPPING: '購物', MOVIE: '睇戲' }
const STATUS = { DRAFT: '草稿', PUBLISHED: '已發佈' }

export default function Dashboard() {
  const [places, setPlaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      setPlaces(await listPlaces())
    } catch (e) {
      setError('載入失敗：' + e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function remove(id, title) {
    if (!window.confirm('確定刪除「' + title + '」？刪咗冇得還原。')) return
    try {
      await deletePlace(id)
      load()
    } catch (e) {
      setError('刪除失敗：' + e.message)
    }
  }

  async function toggleStatus(p) {
    const next = p.status === 'PUBLISHED' ? 'DRAFT' : 'PUBLISHED'
    try {
      await savePlace({ ...p, status: next })
      load()
    } catch (e) {
      setError('狀態更新失敗：' + e.message)
    }
  }

  if (loading) return <p>載入中…</p>

  return (
    <div>
      <div className="row">
        <h2>文章管理（{places.length}）</h2>
        <Link className="btn" to="/new">
          ＋ 新增文章
        </Link>
      </div>
      {error && <p className="error">{error}</p>}
      <table className="tbl">
        <thead>
          <tr>
            <th>標題</th>
            <th>分類</th>
            <th>狀態</th>
            <th>發佈日期</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {places.map((p) => (
            <tr key={p.id}>
              <td>{p.title}</td>
              <td>{CAT[p.category] || p.category}</td>
              <td>
                <span className={'badge ' + String(p.status).toLowerCase()}>{STATUS[p.status] || p.status}</span>
              </td>
              <td>{p.publishedAt ? p.publishedAt.slice(0, 10) : '—'}</td>
              <td className="actions">
                <Link to={'/edit/' + p.id}>編輯</Link>
                <button onClick={() => toggleStatus(p)}>{p.status === 'PUBLISHED' ? '下架' : '發佈'}</button>
                <button className="danger" onClick={() => remove(p.id, p.title)}>
                  刪除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {places.length === 0 && <p>暫時冇文章。</p>}
    </div>
  )
}
