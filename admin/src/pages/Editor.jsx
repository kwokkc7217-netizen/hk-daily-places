import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getPlace, savePlace, uploadImage } from '../api.js'

const EMPTY = {
  title: '',
  slug: '',
  category: 'HIKING',
  status: 'DRAFT',
  description: '',
  mapQuery: '',
  youtubeId: '',
  imageUrl: '',
}

export default function Editor() {
  const { id } = useParams()
  const isNew = !id
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    if (isNew) return
    getPlace(id)
      .then((p) =>
        setForm({
          title: p.title || '',
          slug: p.slug || '',
          category: p.category || 'HIKING',
          status: p.status || 'DRAFT',
          description: p.description || '',
          mapQuery: p.mapQuery || '',
          youtubeId: p.youtubeId || '',
          imageUrl: p.imageUrl || '',
        }),
      )
      .catch((e) => setMsg('載入失敗：' + e.message))
  }, [id, isNew])

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }))
  }

  async function save(e) {
    e.preventDefault()
    setBusy(true)
    setMsg('')
    try {
      await savePlace(isNew ? form : { ...form, id: Number(id) })
      navigate('/')
    } catch (err) {
      setMsg('儲存失敗：' + err.message)
    } finally {
      setBusy(false)
    }
  }

  async function onFile(e) {
    const file = e.target.files && e.target.files[0]
    if (!file) return
    setUploading(true)
    setMsg('')
    try {
      const data = await uploadImage(file)
      set('imageUrl', data.url)
      setMsg('上傳成功')
    } catch (err) {
      setMsg('上傳失敗：' + err.message + '（可直接喺上面貼圖片 URL）')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <h2>{isNew ? '新增文章' : '編輯文章'}</h2>
      {msg && <p className="msg">{msg}</p>}
      <form onSubmit={save} className="form">
        <label>
          標題*
          <input value={form.title} onChange={(e) => set('title', e.target.value)} required />
        </label>
        <label>
          Slug*（網址用，例如 dragon-back）
          <input value={form.slug} onChange={(e) => set('slug', e.target.value)} required />
        </label>
        <div className="row2">
          <label>
            分類
            <select value={form.category} onChange={(e) => set('category', e.target.value)}>
              <option value="HIKING">行山</option>
              <option value="SHOPPING">購物</option>
              <option value="MOVIE">睇戲</option>
            </select>
          </label>
          <label>
            狀態
            <select value={form.status} onChange={(e) => set('status', e.target.value)}>
              <option value="DRAFT">草稿</option>
              <option value="PUBLISHED">已發佈</option>
            </select>
          </label>
        </div>
        <label>
          內文
          <textarea rows="10" value={form.description} onChange={(e) => set('description', e.target.value)} />
        </label>
        <label>
          地圖查詢（例如「龍脊, 香港」）
          <input value={form.mapQuery} onChange={(e) => set('mapQuery', e.target.value)} />
        </label>
        <label>
          YouTube 影片 ID（可空）
          <input value={form.youtubeId} onChange={(e) => set('youtubeId', e.target.value)} />
        </label>
        <label>
          圖片 URL
          <input
            value={form.imageUrl}
            onChange={(e) => set('imageUrl', e.target.value)}
            placeholder="https://…"
          />
        </label>
        {form.imageUrl && <img className="preview" src={form.imageUrl} alt="圖片預覽" />}
        <label>
          或上傳圖片（Cloudinary）
          <input type="file" accept="image/*" onChange={onFile} disabled={uploading} />
        </label>
        {uploading && <p>上傳中…</p>}
        <div className="row">
          <button type="submit" disabled={busy}>
            {busy ? '儲存中…' : '儲存'}
          </button>
          <button type="button" onClick={() => navigate('/')}>
            取消
          </button>
        </div>
      </form>
    </div>
  )
}
