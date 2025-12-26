const TOKEN_CODE = 'access_token'

export function getToken() {
  const token = localStorage.getItem(TOKEN_CODE)
  console.log('从localStorage获取token:', token)
  return token
}

export function setToken(token) {
  console.log('存储token到localStorage:', token)
  localStorage.setItem(TOKEN_CODE, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_CODE)
}

// export async function refreshAccessToken() {
//   const tokenItem = lStorage.getItem(TOKEN_CODE)
//   if (!tokenItem) {
//     return
//   }
//   const { time } = tokenItem
//   // token生成或者刷新后30分钟内不执行刷新
//   if (new Date().getTime() - time <= 1000 * 60 * 30) return
//   try {
//     const res = await api.refreshToken()
//     setToken(res.data.token)
//   } catch (error) {
//     console.error(error)
//   }
// }
