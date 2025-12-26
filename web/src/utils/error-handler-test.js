/**
 * ErrorHandler测试文件
 * 用于验证错误处理机制是否正常工作
 */
import ErrorHandler, { ERROR_TYPES } from './error-handler'

// 测试函数
export function testErrorHandler() {
  console.group('[ErrorHandler Test] 开始测试错误处理机制')

  // 测试1: 网络错误
  console.log('测试1: 网络错误处理')
  const networkError = {
    code: 'NETWORK_ERROR',
    message: '网络连接失败',
  }
  const result1 = ErrorHandler.handle(networkError, { silent: true })
  console.log('网络错误处理结果:', result1)

  // 测试2: 认证错误
  console.log('测试2: 认证错误处理')
  const authError = {
    response: {
      status: 401,
      data: {
        code: 401,
        message: '登录已过期',
        details: {
          error_code: 'AUTHENTICATION_ERROR',
        },
      },
    },
  }
  ErrorHandler.handle(authError, { silent: true }).then((result) => {
    console.log('认证错误处理结果:', result)
  })

  // 测试3: 验证错误
  console.log('测试3: 验证错误处理')
  const validationError = {
    response: {
      status: 422,
      data: {
        code: 422,
        message: '数据验证失败',
        details: {
          error_code: 'VALIDATION_ERROR',
          validation_errors: {
            username: ['用户名不能为空'],
            email: ['邮箱格式不正确'],
          },
        },
      },
    },
  }
  const result3 = ErrorHandler.handle(validationError, { silent: true })
  console.log('验证错误处理结果:', result3)

  // 测试4: 权限错误
  console.log('测试4: 权限错误处理')
  const permissionError = {
    response: {
      status: 403,
      data: {
        code: 403,
        message: '权限不足',
        details: {
          error_code: 'PERMISSION_DENIED',
        },
      },
    },
  }
  const result4 = ErrorHandler.handle(permissionError, { silent: true })
  console.log('权限错误处理结果:', result4)

  console.groupEnd()

  return {
    networkError: result1,
    validationError: result3,
    permissionError: result4,
  }
}

// 在开发环境下自动运行测试
if (import.meta.env.MODE === 'development') {
  // 延迟执行，确保DOM已加载
  setTimeout(() => {
    testErrorHandler()
  }, 1000)
}

export default testErrorHandler
