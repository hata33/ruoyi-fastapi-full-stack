/**
 * 动态路由配置
 * 支持后端动态路由 + 前端硬编码路由相结合
 */

import { FC, lazy, useMemo } from "react";
import { Navigate, useLocation, useRoutes } from "react-router-dom";
import { Button, Result } from "antd";
import { useUser } from "@/context/user";
import Layout from "@/pages/layout/layout";
import HomeView from "@/pages/home/home";
import { COMPONENT_MAP, ROUTE_PATTERN_MAP } from "./componentMap";

// ==================== 组件懒加载 ====================

// 硬编码基础路由的组件
const Login = lazy(() => import("@/pages/login/login"));
const Userinfo = lazy(() => import('@/pages/userinfo.tsx'));
const ChatPage = lazy(() => import('@/pages/chat/ChatPage'));

// ==================== 硬编码的基础路由 ====================

/**
 * 这些路由始终存在，不依赖后端配置
 * 主要包括：首页、聊天、用户中心等核心功能
 */
const STATIC_ROUTES = [
  {
    path: "",
    element: <HomeView />,
  },
  {
    path: "chat",
    element: <ChatPage />,
  },
  {
    path: "chat/:conversationId",  // 支持动态会话ID
    element: <ChatPage />,
  },
  {
    path: "userinfo",
    element: <Userinfo />,
  },
];

// ==================== 动态路由转换函数 ====================

/**
 * 将后端返回的路由数据转换为React Router格式
 * @param backendRoutes 后端返回的路由数据
 * @returns React Router格式的路由配置
 */
function convertBackendRoutes(backendRoutes: any[]): any[] {
  if (!backendRoutes || backendRoutes.length === 0) {
    return [];
  }

  const routes: any[] = [];

  for (const route of backendRoutes) {
    // 跳过隐藏的路由
    if (route.hidden) {
      continue;
    }

    // 构建路由配置
    const routeConfig: any = {
      path: route.path?.startsWith('/') ? route.path.slice(1) : route.path,
    };

    // 处理meta信息
    if (route.meta) {
      routeConfig.meta = route.meta;
    }

    // 处理组件
    if (route.component) {
      // 特殊组件处理
      if (route.component === 'Layout' || route.component === 'ParentView') {
        // Layout和ParentView不需要设置element，由React Router处理
        routeConfig.element = undefined;
      } else if (route.component === 'InnerLink') {
        // 内链使用iframe组件
        routeConfig.element = lazy(() => import('@/components/iframe'));
      } else {
        // 从映射表中查找组件
        const componentKey = route.path?.startsWith('/') ? route.path.slice(1) : route.path;
        const Component = COMPONENT_MAP[componentKey];

        if (Component) {
          routeConfig.element = <Component />;
        } else {
          // 如果没有映射，使用通用占位组件
          console.warn(`未找到组件映射: ${route.component}, path: ${route.path}`);
          routeConfig.element = (
            <Result
              status="warning"
              title="组件未找到"
              subTitle={`路径: ${route.path}, 组件: ${route.component}`}
            />
          );
        }
      }
    }

    // 递归处理子路由
    if (route.children && route.children.length > 0) {
      routeConfig.children = convertBackendRoutes(route.children);
    }

    routes.push(routeConfig);
  }

  return routes;
}

// ==================== 主路由组件 ====================

const Router: FC = () => {
  const location = useLocation();
  const { isLogin, routes: backendRoutes } = useUser();

  // 将后端动态路由转换为React Router格式
  const dynamicRoutes = useMemo(() => {
    return convertBackendRoutes(backendRoutes || []);
  }, [backendRoutes]);

  // 合并静态路由和动态路由
  const mainRoutes = useMemo(() => {
    return [...STATIC_ROUTES, ...dynamicRoutes];
  }, [dynamicRoutes]);

  return useRoutes(
    [
      {
        path: "/",
        element: isLogin ? <Layout /> : <Navigate to="/login" />,
        children: mainRoutes,
      },
      {
        path: "/login",
        element: <Login />,
      },
      {
        path: "*",
        element: (
          <Result
            status="404"
            title="404"
            subTitle="当前页面不存在"
            extra={
              <a href="/">
                <Button type="primary">首页</Button>
              </a>
            }
          />
        ),
      },
    ],
    location
  );
};

export default Router;
