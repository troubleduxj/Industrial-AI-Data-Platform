/**
 * 菜单适配器
 * 用于将后端返回的旧版菜单结构转换为 V5 标准结构
 */

export function adaptToV5(menus) {
  if (!menus || !Array.isArray(menus)) return []

  const adaptedMenus = JSON.parse(JSON.stringify(menus)) // Deep clone

  // DEBUG: Inject Adapter Marker to Root
  adaptedMenus.unshift({
    name: 'V5_ADAPTER_ACTIVE',
    path: '/v5-adapter-active',
    meta: { title: 'V5 Adapter Active', icon: 'check' },
    children: []
  });

  // Helper to find Assets module recursively
  const findAssetsModule = (menuList) => {
    for (const m of menuList) {
      // 1. Check current node
      // Check name/path/title
      const nameMatch = m.path === 'device' || 
        m.name === 'Device' || 
        m.name === 'Device Management' ||
        m.name === 'DeviceManagement' || 
        m.path === '/device' ||
        m.meta?.title === '设备管理' ||
        m.meta?.title === 'Device Management' ||
        m.name === 'Assets' ||
        m.path === '/assets' ||
        m.path === 'assets' ||
        m.meta?.title === '资产' ||
        m.meta?.title === 'Assets';

      if (nameMatch) return m;

      // Check children content (Duck Typing)
      if (m.children && Array.isArray(m.children)) {
        // Helper to check title in meta or root
        const checkTitle = (item, ...titles) => {
          const t = item.meta?.title || item.title || item.name;
          return titles.some(title => t === title || (typeof t === 'string' && t.includes(title)));
        };

        // Check for strong asset signals (Registry, Hierarchy, Maintenance)
        const hasRegistry = m.children.some(c => c.name === 'Registry' || c.path.includes('baseinfo') || checkTitle(c, '资产注册', '设备台账'));
        const hasHierarchy = m.children.some(c => c.name === 'Hierarchy' || c.path.includes('hierarchy') || checkTitle(c, '资产层级', '设备层级'));
        const hasMaintenance = m.children.some(c => c.name === 'Maintenance' || c.path.includes('maintenance') || checkTitle(c, '资产维护', '设备维护'));
        
        // Safety check: Don't mistake System module for Assets module just because it has Dept
        const isSystemLike = (m.name && m.name.toLowerCase().includes('system')) || 
                             (m.path && m.path.toLowerCase().includes('system')) ||
                             checkTitle(m, '系统管理', 'System Management', '平台管理', 'Platform Admin');

        // If it's System-like but has explicit Asset children, we might have found a mixed module or the Assets module is inside.
        // But if it has "Registry" (Asset Registry), it is definitely the Assets module (or the parent of it).
        // Since we are traversing recursively, if the Assets module is a child of System, we will find it when we recurse.
        // So we only return 'm' here if 'm' ITSELF is the Assets module.
        
        // Loose matching: Must have Registry OR Hierarchy. Maintenance is common in System too sometimes.
        if (!isSystemLike && (hasRegistry || hasHierarchy)) {
          console.log('MenuAdapter: Found Assets module by content match:', m.name);
          return m;
        }

        // Recursively check children
        const foundInChildren = findAssetsModule(m.children);
        if (foundInChildren) return foundInChildren;
      }
    }
    return null;
  };

  // 2. Find System Module (for Platform Admin adaptation)
  const findSystemModule = (menuList) => {
    for (const m of menuList) {
      const isSystem = (m.name && m.name.toLowerCase().includes('system')) || 
                       (m.path && m.path.toLowerCase().includes('system')) ||
                       m.meta?.title === '系统管理' ||
                       m.meta?.title === 'System Management' ||
                       m.meta?.title === '平台管理'; // Also match Platform Admin if already renamed
      
      if (isSystem) return m;

      if (m.children && Array.isArray(m.children)) {
        const found = findSystemModule(m.children);
        if (found) return found;
      }
    }
    return null;
  };

  const systemModule = findSystemModule(adaptedMenus);

  if (systemModule) {
    console.log('MenuAdapter: Found System module, adapting to Platform Admin...')
    
    // Rename to Platform Admin
    systemModule.name = 'Platform Admin' 
    systemModule.meta = systemModule.meta || {}
    systemModule.meta.title = 'menu.admin.title'
    systemModule.meta.icon = 'setting'

    // Filter children to keep only standard V5 System modules + Dept
    // We want: Menu, User, Role, Dept, Dict, Param, AuditLog, etc.
    // We explicitly want to REMOVE: Settings, License, Features, Health (as per user complaint)
    
    const allowedChildren = [
      'Menu', 'SystemMenu', 'User', 'Role', 'Dept', 'Department', 
      'Dict', 'Dictionary', 'Param', 'Parameter', 'Audit', 'Log', 'AuditLog'
    ];

    const isAllowed = (c) => {
      const name = c.name || '';
      const title = c.meta?.title || c.title || '';
      // Check whitelist
      if (allowedChildren.some(k => name.includes(k))) return true;
      // Check title keywords
      if (['菜单', '用户', '角色', '部门', '字典', '参数', '日志', '审计'].some(k => typeof title === 'string' && title.includes(k))) return true;
      return false;
    };

    // Filter existing children
    let validChildren = (systemModule.children || []).filter(isAllowed);

    // Ensure Essential Modules Exist (Menu, User, Role)
    const hasMenu = validChildren.some(c => c.name === 'Menu' || c.name === 'SystemMenu' || c.meta?.title === '菜单管理');
    const hasUser = validChildren.some(c => c.name === 'User' || c.meta?.title === '用户管理');
    const hasRole = validChildren.some(c => c.name === 'Role' || c.meta?.title === '角色管理');

    if (!hasMenu) {
      validChildren.unshift({
        name: 'SystemMenu', // Use SystemMenu to avoid conflict
        path: 'menu',
        component: 'system/menu/index',
        meta: { title: 'menu.menu.title', icon: 'menu', keepAlive: true }
      });
    }

    if (!hasUser) {
      validChildren.push({
        name: 'User',
        path: 'user',
        component: 'system/user/index',
        meta: { title: 'menu.user.title', icon: 'user', keepAlive: true }
      });
    }

    if (!hasRole) {
      validChildren.push({
        name: 'Role',
        path: 'role',
        component: 'system/roleV2/index',
        meta: { title: 'menu.role.title', icon: 'lock', keepAlive: true }
      });
    }

    systemModule.children = validChildren;
  }

  const assetsModule = findAssetsModule(adaptedMenus);

  if (assetsModule) {
    try {
      console.log('MenuAdapter: Found Assets module, adapting to V5...')
      console.log('MenuAdapter: Original children:', assetsModule.children)
      
      // Extract original children for mapping
      const originalChildren = assetsModule.children || []
      
      // Helper for finding children
      const findChild = (keywords) => originalChildren.find(c => {
         const t = c.meta?.title || c.title || c.name || '';
         return keywords.some(k => 
           c.path?.includes(k) || 
           t === k || 
           (typeof t === 'string' && t.includes(k))
         );
      });

      const registry = findChild(['baseinfo', 'Registry', '资产注册', '设备台账']);
      const hierarchy = findChild(['hierarchy', 'Hierarchy', '资产层级']);
      const types = findChild(['type', 'Type', 'categories', '设备分类']);
      const monitor = findChild(['monitor', 'Monitor', 'real_time', '设备监测']);
      const maintenance = findChild(['maintenance', 'Maintenance', '资产维护']);
      // Find Dept Management if present (to handle it properly)
      const dept = findChild(['Dept', '部门管理']);

      // Create new children list
      const newChildren = []

      // 1. Asset Explorer (Merge Registry & Hierarchy)
      // Prefer Registry component as base
      // FORCE CREATION: Even if not found, create one if we are in the Assets module
      const explorerBase = registry || hierarchy || originalChildren[0] || { meta: { icon: 'list' } }
      const explorerMeta = explorerBase.meta || {}
      newChildren.push({
        ...explorerBase,
        name: 'AssetExplorer',
        path: 'asset-explorer',
        component: 'assets/AssetExplorer', // Use new V5 component path
        meta: { ...explorerMeta, title: 'menu.asset_explorer.title', icon: 'list' }
      })

      // 2. Asset Types
      if (types) {
        const typesMeta = types.meta || {}
        newChildren.push({
          ...types,
          name: 'AssetTypes',
          path: 'asset-types',
          component: 'assets/AssetTypes', // Use new V5 component path
          meta: { ...typesMeta, title: 'menu.asset_types.title', icon: 'appstore' }
        })
      }

      // 3. Asset Models (New - Reuse Types for now)
      if (types || true) { // Always create
        const typesMeta = types?.meta || {}
        newChildren.push({
          name: 'AssetModels',
          path: 'asset-models',
          component: 'assets/AssetModels', // Use new V5 component path
          meta: { ...typesMeta, title: 'menu.asset_models.title', icon: 'file-text' } 
        })
      }

      // 4. Asset Relations (New - Reuse Explorer for now)
      if (registry || true) { // Always create
        const registryMeta = registry?.meta || {}
        newChildren.push({
          name: 'AssetRelations',
          path: 'asset-relations',
          component: 'assets/AssetRelations', // Use new V5 component path
          meta: { ...registryMeta, title: 'menu.asset_relations.title', icon: 'share-alt' } 
        })
      }

      // 5. Digital Twin (Renamed Monitor)
      if (monitor) {
        const monitorMeta = monitor.meta || {}
        newChildren.push({
          ...monitor,
          name: 'DigitalTwin',
          path: 'digital-twin',
          component: 'assets/DigitalTwin', // Use new V5 component path
          meta: { ...monitorMeta, title: 'menu.digital_twin.title', icon: 'dashboard' }
        })
      }
      
      console.log('MenuAdapter: New children generated:', newChildren)

      // Replace children
      assetsModule.children = newChildren
      
      // Update Assets Module metadata
      assetsModule.name = 'Assets'
      assetsModule.path = '/assets' // Update path to match V5 convention
      
      // Ensure meta object exists and is safe to assign
      if (!assetsModule.meta) {
        assetsModule.meta = {}
      }
      
      // Safe assignment
      if (assetsModule.meta) {
        assetsModule.meta.title = 'menu.assets.title'
        assetsModule.meta.icon = 'hdd'
      }

      // Handle Maintenance Migration
      if (maintenance) {
        // Find or Create "Dashboards & Apps" module
        let appsModule = adaptedMenus.find(m => m.name === 'Dashboards & Apps' || m.path === 'apps')
        
        if (!appsModule) {
          // If not exists, check for "Industrial Apps"
          appsModule = adaptedMenus.find(m => m.name === 'Industrial Apps')
        }

        const maintenanceMeta = maintenance.meta || {}

        if (appsModule) {
          if (!appsModule.children) appsModule.children = []
          appsModule.children.push({
            ...maintenance,
            name: 'MaintenanceApp',
            path: 'maintenance-app',
            meta: { ...maintenanceMeta, title: 'Maintenance App' }
          })
        } else {
          // If no Apps module, maybe append to root as "Industrial Apps"
          // But for now, let's just keep it in Assets if we can't find a home, 
          // OR create a new root module "Industrial Apps"
          adaptedMenus.push({
            name: 'Industrial Apps',
            path: '/industrial-apps',
            component: 'Layout', // Needs to be mapped to Layout component in buildRoutes
            meta: { title: 'Industrial Apps', icon: 'app' },
            children: [{
              ...maintenance,
              name: 'MaintenanceApp',
              path: 'maintenance-app',
              meta: { ...maintenanceMeta, title: 'Maintenance App' }
            }]
          })
        }
      }
    } catch (err) {
      console.error('MenuAdapter: Error during adaptation:', err)
      // Don't throw, just return original to prevent crash
    }
  }

  return adaptedMenus
}
