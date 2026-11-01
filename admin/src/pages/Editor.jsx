import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getPlace, savePlace, uploadImage, listLocations, saveLocation, deleteLocation } from '../api.js'

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

const EMPTY_LOC = { branchName: '', address: '', latitude: '', longitude: '' }

export default function Editor() {
  const { id } = useParams()
  const isNew = !id
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [locations, setLocations] = useState([])
  const [locForm, setLocForm] = useState(EMPTY_LOC)
  const [editingLocId, setEditingLocId] = useState(null)
  const [locBusy, setLocBusy] = useState(false)

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
    refreshLocations()
  }, [id, isNew])

  function refreshLocations() {
    if (isNew) return
    listLocations(id)
      .then(setLocations)
      .catch((e) => setMsg('載入分店失敗：' + e.message))
  }

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

  function setLoc(k, v) {
    setLocForm((f) => ({ ...f, [k]: v }))
  }

  function editLoc(loc) {
    setEditingLocId(loc.id)
    setLocForm({
      branchName: loc.branchName || '',
      address: loc.address || '',
      latitude: loc.latitude ?? '',
      longitude: loc.longitude ?? '',
    })
  }

  function cancelLocEdit() {
    setEditingLocId(null)
    setLocForm(EMPTY_LOC)
  }

  async function submitLoc(e) {
    e.preventDefault()
    const lat = parseFloat(locForm.latitude)
    const lng = parseFloat(locForm.longitude)
    if (!locForm.branchName.trim() || Number.isNaN(lat) || Number.isNaN(lng)) {
      setMsg('分店：分店名、緯度、經度必填，經緯度要係數字')
      return
    }
    setLocBusy(true)
    setMsg('')
    try {
      await saveLocation(id, {
        ...(editingLocId ? { id: editingLocId } : {}),
        branchName: locForm.branchName.trim(),
        address: locForm.address.trim() || null,
        latitude: lat,
        longitude: lng,
      })
      cancelLocEdit()
      refreshLocations()
      setMsg('分店已儲存')
    } catch (err) {
      setMsg('分店儲存失敗：' + err.message)
    } finally {
      setLocBusy(false)
    }
  }

  async function removeLoc(loc) {
    if (!window.confirm(`刪除分店「${loc.branchName}」？`)) return
    setLocBusy(true)
    try {
      await deleteLocation(id, loc.id)
      if (editingLocId === loc.id) cancelLocEdit()
      refreshLocations()
    } catch (err) {
      setMsg('刪除分店失敗：' + err.message)
    } finally {
      setLocBusy(false)
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
              <option value="FOOD">食乜嘢？</option>
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
        {!isNew && (
          <div className="locations">
            <h3>分店（{locations.length}）</h3>
            <p className="hint">
              經緯度：喺 Google Maps 搵到間舖，右鍵 →「這裡有什麼？」就會顯示。冇經緯度嘅分店唔會出現喺地圖上。
            </p>
            {locations.length > 0 && (
              <ul className="loc-list">
                {locations.map((loc) => (
                  <li key={loc.id}>
                    <strong>{loc.branchName}</strong>
                    {loc.address && <span> — {loc.address}</span>}
                    <span className="coords">
                      {' '}
                      ({loc.latitude}, {loc.longitude})
                    </span>
                    <button type="button" onClick={() => editLoc(loc)} disabled={locBusy}>
                      改
                    </button>
                    <button type="button" onClick={() => removeLoc(loc)} disabled={locBusy}>
                      刪
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <form onSubmit={submitLoc} className="loc-form">
              <h4>{editingLocId ? '改分店' : '加分店'}</h4>
              <div className="row2">
                <label>
                  分店名*
                  <input
                    value={locForm.branchName}
                    onChange={(e) => setLoc('branchName', e.target.value)}
                    required
                  />
                </label>
                <label>
                  地址
                  <input value={locForm.address} onChange={(e) => setLoc('address', e.target.value)} />
                </label>
              </div>
              <div className="row2">
                <label>
                  緯度*
                  <input
                    value={locForm.latitude}
                    onChange={(e) => setLoc('latitude', e.target.value)}
                    placeholder="22.29"
                    required
                  />
                </label>
                <label>
                  經度*
                  <input
                    value={locForm.longitude}
                    onChange={(e) => setLoc('longitude', e.target.value)}
                    placeholder="114.17"
                    required
                  />
                </label>
              </div>
              <div className="row">
                <button type="submit" disabled={locBusy}>
                  {locBusy ? '儲存中…' : editingLocId ? '更新分店' : '加分店'}
                </button>
                {editingLocId && (
                  <button type="button" onClick={cancelLocEdit}>
                    取消
                  </button>
                )}
              </div>
            </form>
          </div>
        )}
        {isNew && <p className="hint">分店要先儲存文章後先加得。</p>}
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
