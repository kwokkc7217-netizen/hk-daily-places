// CMS 同 backend 同源（/admin + /api/admin），用 cookie session。
// CSRF 行 cookie 制：Spring 派 XSRF-TOKEN cookie，React 每次 mutating request
// 帶返 X-XSRF-TOKEN header。

function getCsrf() {
  const m = document.cookie.match(/(?:^|; )XSRF-TOKEN=([^;]*)/)
  return m ? decodeURIComponent(m[1]) : ''
}

async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  let payload
  if (body !== undefined && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  } else {
    payload = body
  }
  if (method !== 'GET' && method !== 'HEAD') {
    const token = getCsrf()
    if (token) headers['X-XSRF-TOKEN'] = token
  }
  const res = await fetch(path, { method, headers, body: payload, credentials: 'include' })
  if (res.status === 204) return null
  let data = null
  try {
    data = await res.json()
  } catch (e) {
    // 非 JSON 回應（唔應該發生，但唔好炒）
  }
  if (!res.ok) {
    const err = new Error((data && data.error) || 'HTTP ' + res.status)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

export const me = () => api('/api/admin/me')

export function login(username, password) {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
  const token = getCsrf()
  if (token) headers['X-XSRF-TOKEN'] = token
  return fetch('/api/admin/login', {
    method: 'POST',
    headers,
    body: form,
    credentials: 'include',
  }).then(async (res) => {
    if (!res.ok) {
      const err = new Error('登入失敗')
      err.status = res.status
      throw err
    }
    return res.json()
  })
}

export const logout = () => api('/api/admin/logout', { method: 'POST' })

export const listPlaces = () => api('/api/admin/places')

export const getPlace = (id) => api('/api/admin/places/' + id)

export function savePlace(place) {
  if (place.id) {
    return api('/api/admin/places/' + place.id, { method: 'PUT', body: place })
  }
  return api('/api/admin/places', { method: 'POST', body: place })
}

export function deletePlace(id) {
  return api('/api/admin/places/' + id, { method: 'DELETE' })
}

export function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  return api('/api/admin/upload', { method: 'POST', body: form })
}

export const listUsers = () => api('/api/admin/users')

export const createUser = (username, password) =>
  api('/api/admin/users', { method: 'POST', body: { username, password } })

export const deleteUser = (id) => api('/api/admin/users/' + id, { method: 'DELETE' })

export const changeMyPassword = (password) =>
  api('/api/admin/users/me/password', { method: 'PUT', body: { password } })

export const runSql = (sql) => api('/api/admin/sql', { method: 'POST', body: { sql } })
