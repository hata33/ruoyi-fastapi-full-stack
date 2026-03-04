/**
 * 动态路由组件映射配置
 * 将后端返回的路径映射到前端组件
 */

import { lazy } from "react";

/**
 * 组件映射表
 * key: 后端路由路径 (不含前导斜杠)
 * value: 对应的React组件
 */
export const COMPONENT_MAP: Record<string, React.ComponentType> = {
  // ==================== 系统管理 ====================
  'system/user': lazy(() => import("@/pages/system/user")),
  'system/role': lazy(() => import("@/pages/system/role.tsx")),
  'system/menu': lazy(() => import("@/pages/system/menu")),
  'system/dept': lazy(() => import("@/pages/system/dept.tsx")),
  'system/dict': lazy(() => import("@/pages/system/dict.tsx")),
  'system/dict-data': lazy(() => import("@/pages/system/dictData.tsx")),
  'system/post': lazy(() => import("@/pages/system/post.tsx")),
  'system/config': lazy(() => import("@/pages/system/config.tsx")),
  'system/notice': lazy(() => import("@/pages/system/notice.tsx")),
  'system/log/operlog': lazy(() => import("@/pages/system/log/operlog.tsx")),
  'system/log/logininfor': lazy(() => import("@/pages/system/log/logininfor.tsx")),

  // ==================== 工具模块 ====================
  'tool/gen': lazy(() => import("@/pages/tool/gen.tsx")),

  // ==================== AI对话 ====================
  'deepseek': lazy(() => import('@/pages/deepseek/deepseek.tsx')),

  // ==================== 待办事项 ====================
  'todo/note': lazy(() => import('@/pages/todo/note.tsx')),
  'todo/task': lazy(() => import('@/pages/todo/task.tsx')),
  'todo/category': lazy(() => import('@/pages/todo/category.tsx')),

  // ==================== 每日任务 ====================
  'daily-task': lazy(() => import('@/pages/todo/daily-task.tsx')),
  'daily-task-category': lazy(() => import('@/pages/todo/daily-task-category.tsx')),

  // ==================== 用户信息 ====================
  'userinfo': lazy(() => import('@/pages/userinfo.tsx')),

  // ==================== Chat模块 ====================
  'chat': lazy(() => import('@/pages/chat/ChatPage')),
};

/**
 * 路径到组件的映射（支持参数路由）
 * 用于处理如 /chat/:conversationId 这样的动态路径
 */
export const ROUTE_PATTERN_MAP: Record<string, {
  component: React.ComponentType;
  extractParam?: string; // 需要提取的参数名
}> = {
  'chat': {
    component: lazy(() => import('@/pages/chat/ChatPage')),
    extractParam: 'conversationId',
  },
};

/**
 * 根据路由路径获取对应的组件
 * @param path 路由路径
 * @returns React组件或null
 */
export function getComponentByPath(path: string): React.ComponentType | null {
  // 精确匹配
  if (COMPONENT_MAP[path]) {
    return COMPONENT_MAP[path];
  }

  // 模式匹配（处理动态路由）
  for (const [pattern, config] of Object.entries(ROUTE_PATTERN_MAP)) {
    if (path.startsWith(pattern + '/')) {
      return config.component;
    }
  }

  return null;
}

/**
 * 检查路径是否匹配某个路由模式
 * @param path 要检查的路径
 * @param pattern 路由模式
 * @returns 是否匹配
 */
export function matchRoutePattern(path: string, pattern: string): boolean {
  // 去除开头的斜杠进行匹配
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;

  // 精确匹配
  if (cleanPath === pattern) {
    return true;
  }

  // 前缀匹配（用于动态路由）
  if (cleanPath.startsWith(pattern + '/')) {
    return true;
  }

  return false;
}
