/**
 * JWT解码修复工具
 * 解决'Invalid crypto padding'错误
 *
 * 问题原因：JWT使用base64url编码，而浏览器的atob()函数期望标准base64编码
 * 解决方案：将base64url转换为标准base64，然后再解码
 *
 * @author DeviceMonitorV2 Team
 * @date 2025-01-11
 */

/**
 * 安全的base64url解码函数
 * 解决JWT payload解码时的'Invalid crypto padding'错误
 *
 * @param {string} str - base64url编码的字符串
 * @returns {string} 解码后的字符串
 */
export function safeBase64UrlDecode(str) {
  try {
    // 将base64url转换为标准base64
    // 1. 替换URL安全字符
    let base64 = str.replace(/-/g, '+').replace(/_/g, '/')

    // 2. 添加必要的填充字符
    const padding = base64.length % 4
    if (padding === 2) {
      base64 += '=='
    } else if (padding === 3) {
      base64 += '='
    }

    // 3. 使用标准base64解码
    return atob(base64)
  } catch (error) {
    console.error('Base64URL解码失败:', error)
    throw new Error(`Base64URL解码失败: ${error.message}`)
  }
}

/**
 * 安全的JWT payload解析函数
 *
 * @param {string} token - JWT token
 * @returns {Object} 解析后的payload对象
 */
export function safeParseJWTPayload(token) {
  try {
    if (!token || typeof token !== 'string') {
      throw new Error('Token无效')
    }

    const parts = token.split('.')
    if (parts.length !== 3) {
      throw new Error('JWT格式无效，应该包含3个部分')
    }

    // 使用安全的base64url解码
    const payloadStr = safeBase64UrlDecode(parts[1])
    const payload = JSON.parse(payloadStr)

    return payload
  } catch (error) {
    console.error('JWT payload解析失败:', error)
    throw error
  }
}

/**
 * 安全的JWT header解析函数
 *
 * @param {string} token - JWT token
 * @returns {Object} 解析后的header对象
 */
export function safeParseJWTHeader(token) {
  try {
    if (!token || typeof token !== 'string') {
      throw new Error('Token无效')
    }

    const parts = token.split('.')
    if (parts.length !== 3) {
      throw new Error('JWT格式无效，应该包含3个部分')
    }

    // 使用安全的base64url解码
    const headerStr = safeBase64UrlDecode(parts[0])
    const header = JSON.parse(headerStr)

    return header
  } catch (error) {
    console.error('JWT header解析失败:', error)
    throw error
  }
}

/**
 * 检查token是否过期
 *
 * @param {string} token - JWT token
 * @returns {Object} 检查结果
 */
export function checkTokenExpiration(token) {
  try {
    const payload = safeParseJWTPayload(token)
    const currentTime = Math.floor(Date.now() / 1000)

    if (!payload.exp) {
      return {
        valid: true,
        expired: false,
        message: 'Token没有过期时间设置',
      }
    }

    const expired = payload.exp < currentTime
    const expiresAt = new Date(payload.exp * 1000)

    return {
      valid: !expired,
      expired,
      expiresAt: expiresAt.toISOString(),
      message: expired ? 'Token已过期' : 'Token有效',
      payload,
    }
  } catch (error) {
    return {
      valid: false,
      expired: true,
      error: error.message,
      message: 'Token解析失败',
    }
  }
}

/**
 * 验证token格式
 *
 * @param {string} token - JWT token
 * @returns {Object} 验证结果
 */
export function validateTokenFormat(token) {
  try {
    if (!token || typeof token !== 'string') {
      return {
        valid: false,
        error: 'Token为空或格式无效',
      }
    }

    const parts = token.split('.')
    if (parts.length !== 3) {
      return {
        valid: false,
        error: `JWT应该包含3个部分，当前包含${parts.length}个部分`,
      }
    }

    // 尝试解析header和payload
    const header = safeParseJWTHeader(token)
    const payload = safeParseJWTPayload(token)

    return {
      valid: true,
      header,
      payload,
      message: 'Token格式有效',
    }
  } catch (error) {
    return {
      valid: false,
      error: error.message,
    }
  }
}

/**
 * 替换原有的不安全解码方法
 * 这个函数可以直接替换代码中的 JSON.parse(atob(tokenParts[1]))
 *
 * @param {string} token - JWT token
 * @returns {Object} 解析后的payload
 */
export function decodeJWTPayload(token) {
  return safeParseJWTPayload(token)
}

/**
 * 调试函数：显示token的详细信息
 *
 * @param {string} token - JWT token
 */
export function debugToken(token) {
  console.group('🔍 JWT Token调试信息')

  try {
    const validation = validateTokenFormat(token)
    console.log('格式验证:', validation)

    if (validation.valid) {
      const expiration = checkTokenExpiration(token)
      console.log('过期检查:', expiration)

      console.log('Header:', validation.header)
      console.log('Payload:', validation.payload)
    }
  } catch (error) {
    console.error('调试失败:', error)
  }

  console.groupEnd()
}
