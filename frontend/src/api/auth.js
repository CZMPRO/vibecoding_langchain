import http from './http'

export function loginApi(data) {
  return http.post('/auth/login', data)
}

export function registerApi(data) {
  return http.post('/auth/register', data)
}

export function meApi() {
  return http.get('/auth/me')
}

export function changePasswordApi(data) {
  return http.post('/auth/change-password', data)
}
