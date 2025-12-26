import { createPageLoadingGuard } from './page-loading-guard'
import { createPageTitleGuard } from './page-title-guard'
import { createAuthGuard } from './auth-guard'
import { createPermissionGuard } from './permission-guard'

export function setupRouterGuard(router) {
  createPageLoadingGuard(router)
  createAuthGuard(router)
  createPermissionGuard(router)
  createPageTitleGuard(router)
}
