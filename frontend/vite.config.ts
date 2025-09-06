import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// 統合された稼働.com設定ファイル
// プロジェクト全体の設定をここに集約
export default defineConfig(({ mode }) => {
  // 環境変数を読み込む
  const env = loadEnv(mode, process.cwd())
  
  // プロジェクト共通設定
  const config = {
    appName: '稼働.com',
    apiBaseUrl: env.VITE_API_BASE_URL || 'http://localhost:8000',
    port: parseInt(env.VITE_PORT || '3000'),
    isDev: mode === 'development'
  }
  
  return {
    // プラグイン
    plugins: [react()],
    
    // パス解決設定
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    
    // 開発サーバー設定
    server: {
      port: config.port,
      host: true, // ネットワークからアクセス可能にする
      proxy: {
        // APIリクエストのプロキシ設定
        '/api': {
          target: config.apiBaseUrl,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    
    // ビルド設定
    build: {
      outDir: 'dist',
      minify: !config.isDev,
      sourcemap: config.isDev,
    },
    
    // グローバル変数定義
    define: {
      __APP_NAME__: JSON.stringify(config.appName),
      __API_URL__: JSON.stringify(config.apiBaseUrl),
      __DEV__: config.isDev
    },
    
    // CSS設定 (PostCSS, Tailwindの設定を統合)
    css: {
      postcss: {
        plugins: [
          require('tailwindcss'),
          require('autoprefixer')
        ]
      }
    }
  }
})
