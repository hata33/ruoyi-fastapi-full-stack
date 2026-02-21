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
          target: env.VITE_API_TARGET || "http://localhost:8001",
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/dev-api/, ""),
        },
        "/profile": {
          target: env.VITE_PROFILE_TARGET || "http://localhost:8001",
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
