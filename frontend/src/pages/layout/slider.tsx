import { FC, useCallback, useMemo, useState, ReactElement } from "react";
import { Menu, Typography } from "antd";
import { useLocation, useNavigate } from "react-router-dom";
import { useAppTheme } from "@/context/theme";
import { useUser } from "@/context/user";
import * as icons from '@ant-design/icons';
import logo from './x.png';


interface MenuItem {
  key: string;
  icon: ReactElement;
  label: string;
  children?: MenuItem[];
}

/**
 * 将后端路由转换为菜单项
 */
function convertRouteToMenu(route: any, parentPath = ""): MenuItem | null {
  // 跳过隐藏路由
  if (route.hidden) {
    return null;
  }

  // 跳过没有meta信息的路由（通常是布局路由）
  if (!route.meta && !route.children) {
    return null;
  }

  // 获取图标
  const iconStr = route.meta?.icon;
  const Icon = iconStr ? (icons as any)[iconStr] : undefined;

  // 构建当前菜单项的key
  const currentPath = parentPath ? `${parentPath}/${route.path}` : `/${route.path}`;

  const menu: MenuItem = {
    key: currentPath,
    icon: Icon ? <Icon /> : <icons.AppstoreOutlined />,
    label: route.meta?.title || route.path,
  };

  // 递归处理子路由
  if (route.children && route.children.length > 0) {
    menu.children = [];
    for (const child of route.children) {
      const childMenu = convertRouteToMenu(child, currentPath);
      if (childMenu) {
        menu.children.push(childMenu);
      }
    }

    // 如果没有子菜单，删除children属性
    if (menu.children.length === 0) {
      delete menu.children;
    }
  }

  return menu;
}

/**
 * 合并静态菜单和动态菜单
 */
function mergeMenus(staticMenus: MenuItem[], dynamicRoutes: any[]): MenuItem[] {
  const allMenus: MenuItem[] = [...staticMenus];

  // 添加动态路由生成的菜单
  if (dynamicRoutes && dynamicRoutes.length > 0) {
    for (const route of dynamicRoutes) {
      const menu = convertRouteToMenu(route);
      if (menu) {
        allMenus.push(menu);
      }
    }
  }

  return allMenus;
}

// ==================== 静态硬编码菜单 ====================
// 移到组件外部，避免每次渲染重新创建

const staticMenus: MenuItem[] = [
  {
    key: "/",
    icon: <icons.HomeOutlined />,
    label: "首页",
  },
  {
    key: "/chat-menu",
    icon: <icons.MessageOutlined />,
    label: "AI 对话",
    children: [
      {
        key: "/chat",
        icon: <icons.WechatOutlined />,
        label: "新建对话",
      },
    ],
  },
];

const Slider: FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const { slideExpand } = useAppTheme();
  const { routes: backendRoutes } = useUser();

  const [isScroll, setIsScroll] = useState(false);

  // ==================== 处理菜单点击 ====================

  const handleMenuClick = useCallback((key: string) => {
    // 聊天菜单在新标签页打开全屏页面
    if (key === '/chat') {
      window.open('/chat', '_blank');
      return;
    }
    // 其他路由正常导航
    if (location.pathname !== key) {
      navigate(key);
    }
  }, [navigate, location.pathname]);

  // ==================== 合并所有菜单 ====================

  const menus = useMemo(() => {
    return mergeMenus(staticMenus, backendRoutes || []);
  }, [backendRoutes]);

  // ==================== 计算当前展开的菜单 ====================

  const openKeys = useMemo(() => {
    if (location.pathname === "/") return ["/"];

    const keys: string[] = [];

    // 递归查找包含当前路径的菜单
    const findOpenKeys = (menuList: MenuItem[]) => {
      for (const menu of menuList) {
        if (location.pathname.startsWith(menu.key)) {
          keys.push(menu.key);
        }
        if (menu.children?.length) {
          findOpenKeys(menu.children);
        }
      }
    };

    findOpenKeys(menus);
    return keys;
  }, [location, menus]);

  const menuScroll = useCallback((e: any) => {
    setIsScroll(e.target.scrollTop > 0);
  }, []);

  return (
    <div className="slider" style={{ width: slideExpand ? 220 : 79 }}>
      <a href="/" className={isScroll ? "border" : ""}>
        <img
          src={logo}
          alt=""
        />
        {slideExpand ? (
          <Typography.Title style={{ paddingLeft: 0, marginBottom: 0 }} level={4}>
            X-Admin
          </Typography.Title>
        ) : (
          ""
        )}
      </a>

      <div className="menus" onScroll={menuScroll}>
        <Menu
          selectedKeys={[location.pathname.includes('/system/dict') ? '/system/dict' : location.pathname]}
          items={menus as any}
          theme="light"
          defaultOpenKeys={openKeys}
          subMenuOpenDelay={0.3}
          style={{ background: "inherit" }}
          mode="inline"
          inlineCollapsed={!slideExpand}
          onClick={(item) => {
            handleMenuClick(item.key as string);
          }}
        />
      </div>
    </div>
  );
};

export default Slider;
