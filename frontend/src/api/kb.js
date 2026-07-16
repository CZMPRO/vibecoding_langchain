import http from './http'

export function listDocumentsApi(params) {
  return http.get('/kb/documents', { params })
}

export function uploadDocumentApi(file, onUploadProgress) {
  const form = new FormData()
  form.append('file', file)
  return http.post('/kb/documents', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
}

export function deleteDocumentApi(id) {
  return http.delete(`/kb/documents/${id}`)
}

export function retryDocumentApi(id) {
  return http.post(`/kb/documents/${id}/retry`)
}

export function statsOverviewApi() {
  return http.get('/stats/overview')
}
