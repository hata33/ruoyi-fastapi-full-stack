# Markdown 渲染快速参考指南

## 快速开始

```tsx
import MarkdownRenderer from '@/pages/chat/components/MarkdownRenderer';

// 基础使用
<MarkdownRenderer content="# Hello\n\n这是 Markdown 内容" />

// 流式渲染
<MarkdownRenderer content={streamingContent} isStreaming={true} />

// 自定义样式
<MarkdownRenderer
  content={content}
  className="custom-prose"
/>
```

## 支持的 Markdown 语法

### 📝 基础语法

| 语法 | Markdown | 效果 |
|------|----------|------|
| 标题 | `# H1` ~ `###### H6` | 不同大小的标题 |
| 粗体 | `**粗体**` | **粗体** |
| 斜体 | `*斜体*` | *斜体* |
| 删除线 | `~~删除~~` | ~~删除~~ |
| 引用 | `> 引用` | 引用块 |
| 代码 | `` `代码` `` | `行内代码` |
| 链接 | `[文本](url)` | [链接](url) |
| 图片 | `![alt](url)` | 图片 |

### 🎯 GitHub 风格 (GFM)

| 语法 | 示例 |
|------|------|
| 表格 | `\| 列1 \| 列2 \|` |
| 任务列表 | `- [x] 已完成` |
| 自动链接 | `https://example.com` |

### 🔢 数学公式 (LaTeX)

| 类型 | 语法 | 示例 |
|------|------|------|
| 行内公式 | `$公式$` | `$E=mc^2$` |
| 块级公式 | `$$公式$$` | `$$\int_0^\infty$$` |

**常用数学符号**：
```
上标: x^2
下标: x_1
分数: \frac{a}{b}
根号: \sqrt{x}
求和: \sum_{i=1}^n
积分: \int_a^b
希腊字母: \alpha, \beta, \gamma, \delta
```

### 💻 代码块

``````markdown
```语言名称
代码内容
```
``````

**支持的语言**：
```
typescript, javascript, python, java, go, rust, cpp, csharp
php, html, css, json, yaml, sql, bash, shell
markdown, docker, nginx, etc.
```

## 样式定制

### Tailwind CSS 类名

```tsx
// 自定义容器样式
<MarkdownRenderer
  content={content}
  className="prose prose-sm dark:prose-invert max-w-2xl"
/>

// 移除默认样式
<MarkdownRenderer
  content={content}
  className="!max-w-none"
/>
```

### 自定义组件

在 `MarkdownRenderer.tsx` 中修改 `components` 配置：

```typescript
const components = {
  // 自定义标题样式
  h1: ({ children }) => (
    <h1 className="text-3xl font-bold text-red-500">
      {children}
    </h1>
  ),

  // 自定义链接样式
  a: ({ children, href }) => (
    <a href={href} className="text-blue-500 hover:underline">
      {children}
    </a>
  ),
};
```

## 流式渲染处理

### 自动修复的语法问题

```typescript
// 不完整的代码块会被自动补全
console.log('Hello'  // 自动添加: ```

// 不完整的数学公式会被自动补全
$x = 1  // 自动添加: $
```

### 流式渲染效果

```tsx
// 显示光标
<MarkdownRenderer
  content={partialContent}
  isStreaming={true}  // 显示打字机光标
/>
```

## 性能优化

### 1. 内容长度限制

```typescript
const MAX_LENGTH = 100000; // 100KB

if (content.length > MAX_LENGTH) {
  return <div>内容过长，无法显示</div>;
}
```

### 2. 防抖处理

```typescript
import { useDebounce } from '@/hooks/useDebounce';

const debouncedContent = useDebounce(content, 100);

<MarkdownRenderer content={debouncedContent} />
```

### 3. 虚拟滚动（大量内容）

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={messages.length}
  itemSize={100}
>
  {({ index }) => (
    <MarkdownRenderer content={messages[index].content} />
  )}
</FixedSizeList>
```

## 常见问题

### ❌ 数学公式不显示

**原因**：缺少 KaTeX 样式

**解决**：
```typescript
import 'katex/dist/katex.min.css';
```

### ❌ 代码不高亮

**原因**：语言标识错误

**解决**：
````markdown
```typescript  // ✅ 正确
`````unknown    // ❌ 错误
``````

### ❌ 表格显示异常

**原因**：未启用 GFM 插件

**解决**：确认 `remarkPlugins` 包含 `remarkGfm`

### ❌ HTML 标签被转义

**原因**：未启用 `rehype-raw`

**解决**：确认 `rehypePlugins` 包含 `rehypeRaw`

## 调试技巧

### 1. 查看渲染时间

```typescript
console.time('MarkdownRender');
<MarkdownRenderer content={content} />;
console.timeEnd('MarkdownRender');
```

### 2. 检查插件加载

```typescript
console.log('Remark plugins:', [
  'remarkGfm',
  'remarkMath',
  'remarkBreaks',
]);

console.log('Rehype plugins:', [
  'rehypeKatex',
  'rehypeRaw',
]);
```

### 3. 验证内容预处理

```typescript
console.log('Original:', content.length);
console.log('Processed:', processedContent.length);
console.log('Diff:', processedContent.substring(0, 200));
```

## 示例代码

### 完整示例

```tsx
import React, { useState } from 'react';
import MarkdownRenderer from '@/pages/chat/components/MarkdownRenderer';

function Example() {
  const [content, setContent] = useState(`
# 欢迎使用 AI 聊天

这是一个支持 **丰富 Markdown** 语法的聊天应用。

## 功能特性

- [x] 完整的 Markdown 支持
- [ ] 数学公式渲染
- [ ] 代码高亮

## 数学公式示例

行内公式：$E = mc^2$

块级公式：
$$
f(x) = \\int_{-\\infty}^{\\infty} \\hat{f}(\\xi)\\,e^{2\\pi i \\xi x} \\,d\\xi
$$

## 代码示例

\`\`\`typescript
interface User {
  id: number;
  name: string;
  email: string;
}

const user: User = {
  id: 1,
  name: 'Alice',
  email: 'alice@example.com',
};
\`\`\`

## 表格示例

| 功能 | 状态 | 说明 |
|------|------|------|
| Markdown | ✅ | 完全支持 |
| 数学公式 | ✅ | KaTeX 渲染 |
| 代码高亮 | ✅ | 多语言支持 |
  `);

  return (
    <div className="p-6">
      <MarkdownRenderer content={content} />
    </div>
  );
}
```

## API 参考

### MarkdownRenderer Props

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `content` | `string` | ✅ | - | Markdown 内容 |
| `className` | `string` | ❌ | - | 自定义样式类名 |
| `isStreaming` | `boolean` | ❌ | `false` | 是否流式渲染 |

## 相关文档

- [完整技术文档](./Dify技术栈实现文档.md)
- [API 设计文档](../../api-design/01-chat/API设计文档.md)
- [组件设计文档](../../frontend-design/01-chat/02-组件拆分设计.md)

---

**快速参考** v1.0 | 最后更新: 2026-03-03
