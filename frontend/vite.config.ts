import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": "/src",
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          api: "modern-compiler",
        },
      },
    },
    server: {
      port: Number(env.VITE_PORT) || 5173,
      proxy: {
        "/dev-api": {
          target: env.VITE_API_TARGET || "http://localhost:9099",
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/dev-api/, ""),
          // 支持 SSE 流式响应
          configure: (proxy, _options) => {
            proxy.on('proxyReq', (proxyReq, _req, _res) => {
              // 不对请求做任何修改
            });
            proxy.on('proxyRes', (proxyRes, _req, _res) => {
              // SSE 响应不缓冲
              if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
                proxyRes.headers['x-accel-buffering'] = 'no';
              }
            });
          },
        },
        "/profile": {
          target: env.VITE_PROFILE_TARGET || "http://localhost:9099",
          changeOrigin: true,
        },
        "/deepseekr1": {
          target: env.VITE_DEEPSEEKR1_TARGET || "https://h.xmw.monster",
          changeOrigin: true,
        },
      },
    },
  };
});
