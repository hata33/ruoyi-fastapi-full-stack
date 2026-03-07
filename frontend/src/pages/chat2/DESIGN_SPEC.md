# Chat2 新拟物风格设计规范

## 1. 设计理念

新拟物风格的核心特征：
- **柔和的阴影**：利用明暗两个方向的阴影营造立体感
- **圆润的边角**：大圆角设计增强柔和感
- **低对比度**：颜色饱和度低，视觉舒适
- **浮雕效果**：通过阴影变化实现凸起和凹陷的视觉效果

## 2. 色彩系统

### 2.1 基础色板

```css
/* 背景色 - 柔和的浅灰色 */
--soft-bg-light: #e8eef5;
--soft-bg-dark: #1a1f2c;

/* 元素色 - 与背景相近但略亮 */
--soft-element-light: #e8eef5;
--soft-element-dark: #242b3d;

/* 文字色 - 低对比度灰色 */
--soft-text-light: #5a6b7c;
--soft-text-dark: #8b9bb3;

/* 强调色 - 柔和的蓝紫色 */
--soft-accent: #6b7fd7;
--soft-accent-hover: #5a6bc4;
```

### 2.2 Tailwind 配置

```javascript
colors: {
  soft: {
    bg: {
      light: '#e8eef5',
      DEFAULT: '#e8eef5',
      dark: '#1a1f2c',
    },
    element: {
      light: '#e8eef5',
      DEFAULT: '#e8eef5',
      dark: '#242b3d',
    },
    text: {
      light: '#5a6b7c',
      DEFAULT: '#5a6b7c',
      dark: '#8b9bb3',
    },
    accent: {
      DEFAULT: '#6b7fd7',
      hover: '#5a6bc4',
    },
  },
}
```

## 3. 阴影系统

新拟物风格的核心是通过双重阴影实现浮雕效果：

### 3.1 阴影定义

```css
/* 凸起效果 - 小 */
--shadow-neu-sm:
  6px 6px 12px rgba(163, 177, 198, 0.4),
  -6px -6px 12px rgba(255, 255, 255, 0.8);

/* 凸起效果 - 中 */
--shadow-neu:
  8px 8px 16px rgba(163, 177, 198, 0.5),
  -8px -8px 16px rgba(255, 255, 255, 0.9);

/* 凸起效果 - 大 */
--shadow-neu-lg:
  12px 12px 24px rgba(163, 177, 198, 0.6),
  -12px -12px 24px rgba(255, 255, 255, 1);

/* 凹陷效果 - 小 */
--shadow-neu-inset-sm:
  inset 4px 4px 8px rgba(163, 177, 198, 0.4),
  inset -4px -4px 8px rgba(255, 255, 255, 0.8);

/* 凹陷效果 - 中 */
--shadow-neu-inset:
  inset 6px 6px 12px rgba(163, 177, 198, 0.5),
  inset -6px -6px 12px rgba(255, 255, 255, 0.9);
```

### 3.2 Tailwind 阴影配置

```javascript
boxShadow: {
  'neu-sm': '6px 6px 12px rgba(163, 177, 198, 0.4), -6px -6px 12px rgba(255, 255, 255, 0.8)',
  'neu': '8px 8px 16px rgba(163, 177, 198, 0.5), -8px -8px 16px rgba(255, 255, 255, 0.9)',
  'neu-lg': '12px 12px 24px rgba(163, 177, 198, 0.6), -12px -12px 24px rgba(255, 255, 255, 1)',
  'neu-inset-sm': 'inset 4px 4px 8px rgba(163, 177, 198, 0.4), inset -4px -4px 8px rgba(255, 255, 255, 0.8)',
  'neu-inset': 'inset 6px 6px 12px rgba(163, 177, 198, 0.5), inset -6px -6px 12px rgba(255, 255, 255, 0.9)',
}
```

## 4. 组件样式规范

### 4.1 卡片 (Card)

```html
<div class="bg-soft-element rounded-3xl shadow-neu p-6">
  <h2 class="text-soft-text text-xl font-medium mb-4">Card Title</h2>
  <p class="text-soft-text opacity-80">内容文字，注意对比度。</p>
</div>
```

**状态变体：**
- 悬浮：`hover:shadow-neu-lg`
- 按下：`active:shadow-neu-inset-sm`

### 4.2 按钮 (Button)

**主要按钮：**
```html
<button class="bg-soft-element px-6 py-3 rounded-2xl shadow-neu-sm text-soft-text font-medium transition-shadow duration-200 hover:shadow-neu focus:outline-none active:shadow-neu-inset-sm">
  点击
</button>
```

**强调按钮：**
```html
<button class="bg-soft-accent px-6 py-3 rounded-2xl shadow-neu-sm text-white font-medium transition-shadow duration-200 hover:bg-soft-accent-hover active:shadow-neu-inset-sm">
  确认
</button>
```

**图标按钮：**
```html
<button class="bg-soft-element w-10 h-10 rounded-xl shadow-neu-sm flex items-center justify-center text-soft-text hover:shadow-neu active:shadow-neu-inset-sm transition-shadow duration-200">
  <icon />
</button>
```

### 4.3 输入框 (Input)

```html
<input type="text" placeholder="输入..."
       class="w-full bg-soft-element px-4 py-3 rounded-xl shadow-neu-inset-sm text-soft-text placeholder-soft-text/50 focus:shadow-neu-inset focus:outline-none transition-shadow duration-200">
```

**多行文本域：**
```html
<textarea placeholder="输入内容..."
          class="w-full bg-soft-element px-4 py-3 rounded-xl shadow-neu-inset-sm text-soft-text placeholder-soft-text/50 focus:shadow-neu-inset focus:outline-none resize-none transition-shadow duration-200"></textarea>
```

### 4.4 开关 (Toggle)

```html
<label class="relative inline-block w-16 h-8 cursor-pointer">
  <input type="checkbox" class="opacity-0 w-0 h-0 peer">
  <span class="absolute inset-0 bg-soft-element rounded-full shadow-neu-sm transition-all duration-300 peer-checked:shadow-neu-inset-sm before:content-[''] before:absolute before:h-6 before:w-6 before:left-1 before:bottom-1 before:bg-soft-element before:rounded-full before:shadow-neu-sm peer-checked:before:translate-x-8 peer-checked:before:bg-soft-accent"></span>
</label>
```

### 4.5 滑块 (Slider)

```html
<input type="range" min="0" max="100"
       class="w-full h-2 bg-soft-element rounded-full shadow-neu-inset-sm appearance-none cursor-pointer
              [&::-webkit-slider-thumb]:appearance-none
              [&::-webkit-slider-thumb]:w-5
              [&::-webkit-slider-thumb]:h-5
              [&::-webkit-slider-thumb]:rounded-full
              [&::-webkit-slider-thumb]:bg-soft-element
              [&::-webkit-slider-thumb]:shadow-neu-sm
              [&::-webkit-slider-thumb]:transition-all
              [&::-webkit-slider-thumb]:duration-200
              [&::-webkit-slider-thumb]:hover:shadow-neu">
```

### 4.6 消息气泡 (Message Bubble)

**用户消息：**
```html
<div class="bg-soft-element rounded-2xl rounded-tr-sm shadow-neu px-4 py-3 text-soft-text max-w-[80%]">
  用户消息内容
</div>
```

**AI 消息：**
```html
<div class="bg-soft-element rounded-2xl rounded-tl-sm shadow-neu-inset-sm px-4 py-3 text-soft-text max-w-[80%]">
  AI 回复内容
</div>
```

### 4.7 侧边栏 (Sidebar)

```html
<div class="bg-soft-bg h-full p-4 space-y-4">
  <!-- 会话列表 -->
  <div class="bg-soft-element rounded-2xl shadow-neu-inset-sm p-4">
    <h3 class="text-soft-text font-medium mb-3">会话列表</h3>
    <div class="space-y-2">
      <!-- 会话项 -->
      <div class="bg-soft-element rounded-xl shadow-neu-sm px-3 py-2 text-soft-text text-sm cursor-pointer hover:shadow-neu transition-shadow duration-200">
        会话标题
      </div>
    </div>
  </div>
</div>
```

### 4.8 头部 (Header)

```html
<header class="bg-soft-element shadow-neu px-6 py-4">
  <div class="flex items-center justify-between">
    <h1 class="text-soft-text text-xl font-medium">AI Chat</h1>
    <div class="flex items-center space-x-3">
      <!-- 操作按钮 -->
      <button class="bg-soft-element w-10 h-10 rounded-xl shadow-neu-sm flex items-center justify-center text-soft-text hover:shadow-neu active:shadow-neu-inset-sm transition-all duration-200">
        <icon />
      </button>
    </div>
  </div>
</header>
```

## 5. 布局规范

### 5.1 间距系统

使用 Tailwind 默认间距，偏好：
- `p-4` / `px-4` / `py-4` - 标准内边距
- `space-y-4` / `space-x-4` - 元素间距
- `gap-4` - Flex/Grid 间距

### 5.2 圆角规范

```javascript
borderRadius: {
  'neu-sm': '0.75rem',   // 12px - 小元素
  'neu': '1rem',         // 16px - 标准元素
  'neu-lg': '1.25rem',   // 20px - 大元素
  'neu-xl': '1.5rem',    // 24px - 卡片
  'neu-2xl': '1.75rem',  // 28px - 面板
}
```

### 5.3 响应式断点

- 移动端：`< 768px`
- 平板端：`768px - 1024px`
- 桌面端：`> 1024px`

## 6. 动画规范

### 6.1 过渡时间

- 交互反馈：`duration-200` (200ms)
- 状态变化：`duration-300` (300ms)
- 页面切换：`duration-500` (500ms)

### 6.2 缓动函数

- 标准过渡：`ease-out`
- 弹性效果：`ease-out-back`
- 平滑效果：`ease-in-out`

## 7. 暗色模式

### 7.1 暗色模式阴影

```css
/* 暗色模式 - 凸起效果 */
--shadow-neu-sm-dark:
  6px 6px 12px rgba(0, 0, 0, 0.4),
  -6px -6px 12px rgba(66, 71, 82, 0.4);

/* 暗色模式 - 凹陷效果 */
--shadow-neu-inset-sm-dark:
  inset 4px 4px 8px rgba(0, 0, 0, 0.4),
  inset -4px -4px 8px rgba(66, 71, 82, 0.4);
```

### 7.2 暗色模式实现

使用 Tailwind 的 `dark:` 前缀：

```html
<div class="bg-soft-bg-light dark:bg-soft-bg-dark shadow-neu-sm dark:shadow-neu-sm-dark">
  <!-- 内容 -->
</div>
```

## 8. 可访问性

### 8.1 文字对比度

- 标题文字：使用较深的 `soft-text` 颜色
- 正文文字：保持至少 4.5:1 的对比度
- 禁用文字：使用 `opacity-50` 降低对比度

### 8.2 交互状态

- **焦点状态**：增加边框或阴影变化
- **悬浮状态**：阴影加深或轻微位移
- **按下状态**：凹陷效果
- **禁用状态**：降低透明度和移除阴影效果

### 8.3 焦点指示器

```css
.focus-visible:focus {
  outline: 2px solid var(--soft-accent);
  outline-offset: 2px;
}
```

## 9. 滚动条样式

```css
/* 新拟物风格滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d9e6;
  border-radius: 4px;
  box-shadow: inset 1px 1px 2px rgba(163, 177, 198, 0.4),
              inset -1px -1px 2px rgba(255, 255, 255, 0.8);
}

::-webkit-scrollbar-thumb:hover {
  background: #c5cdd8;
}

.dark ::-webkit-scrollbar-thumb {
  background: #3a4150;
  box-shadow: inset 1px 1px 2px rgba(0, 0, 0, 0.4),
              inset -1px -1px 2px rgba(66, 71, 82, 0.4);
}
```

## 10. CSS 类名速查表

| 组件 | 类名 |
|------|------|
| 背景 | `bg-soft-bg-light dark:bg-soft-bg-dark` |
| 元素背景 | `bg-soft-element` |
| 文字颜色 | `text-soft-text-light dark:text-soft-text-dark` |
| 凸起阴影 | `shadow-neu-sm` / `shadow-neu` / `shadow-neu-lg` |
| 凹陷阴影 | `shadow-neu-inset-sm` / `shadow-neu-inset` |
| 标准圆角 | `rounded-2xl` / `rounded-3xl` |
| 输入框 | `shadow-neu-inset-sm focus:shadow-neu-inset` |
| 按钮 | `shadow-neu-sm hover:shadow-neu active:shadow-neu-inset-sm` |
| 强调按钮 | `bg-soft-accent hover:bg-soft-accent-hover` |
