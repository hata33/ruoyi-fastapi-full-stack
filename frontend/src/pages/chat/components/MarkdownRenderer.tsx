/**
 * Markdown Renderer Component
 * Markdown 渲染器组件 - 使用 Dify 相同技术栈
 *
 * 技术栈：
 * - react-markdown: 基础渲染器
 * - remark-gfm: GitHub 风格 Markdown（表格、任务列表等）
 * - remark-math: 数学公式支持
 * - remark-breaks: 换行支持
 * - rehype-katex: KaTeX 数学公式渲染
 * - rehype-raw: HTML 标签支持
 * - react-syntax-highlighter: 代码高亮
 */

import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkBreaks from 'remark-breaks';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn } from '@/utils/cn';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  isStreaming?: boolean;
}

/**
 * Markdown 渲染器组件
 * 支持：
 * - 标准 Markdown 语法
 * - GitHub 风格 Markdown (GFM): 表格、任务列表、删除线
 * - 数学公式: $inline$ 和 $$block$$
 * - 代码高亮: 支持多种语言
 * - 流式渲染: 打字机效果
 */
const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className,
  isStreaming = false,
}) => {
  // 预处理内容：处理流式渲染中的不完整语法
  const processedContent = useMemo(() => {
    if (!content) return '';

    let processed = content;

    // 修复流式渲染中的代码块
    // 如果有不完整的代码块，临时补全
    const codeBlockCount = (processed.match(/```/g) || []).length;
    if (codeBlockCount % 2 !== 0) {
      processed += '\n```';
    }

    // 修复流式渲染中的数学公式
    const inlineMathCount = (processed.match(/\$/g) || []).length;
    if (inlineMathCount % 2 !== 0) {
      processed += ' $';
    }

    return processed;
  }, [content]);

  // 自定义组件映射
  const components = {
    // 代码块渲染
    code: ({ node, inline, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';

      return !inline && language ? (
        <div className="relative group my-4">
          {/* 代码头部：语言标识和复制按钮 */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 dark:bg-gray-900 rounded-t-lg border-b border-gray-700">
            <span className="text-xs text-gray-400 font-mono">{language}</span>
            <CopyButton content={String(children).replace(/\n$/, '')} />
          </div>
          {/* 代码内容 */}
          <SyntaxHighlighter
            style={vscDarkPlus}
            language={language}
            PreTag="div"
            className="!bg-gray-900 !p-4 !text-xs rounded-b-lg !m-0"
            {...props}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code
          className={cn(
            'px-1.5 py-0.5 rounded',
            'bg-gray-200 dark:bg-gray-700',
            'text-gray-800 dark:text-gray-200',
            'text-xs font-mono',
            'before:content-["`"] after:content-["`"]',
          )}
          {...props}
        >
          {children}
        </code>
      );
    },

    // 标题渲染
    h1: ({ children, ...props }: any) => (
      <h1 className="text-2xl font-bold mb-4 mt-6 pb-2 border-b border-gray-200 dark:border-gray-700" {...props}>
        {children}
      </h1>
    ),
    h2: ({ children, ...props }: any) => (
      <h2 className="text-xl font-bold mb-3 mt-5" {...props}>
        {children}
      </h2>
    ),
    h3: ({ children, ...props }: any) => (
      <h3 className="text-lg font-semibold mb-2 mt-4" {...props}>
        {children}
      </h3>
    ),

    // 段落渲染
    p: ({ children, ...props }: any) => (
      <p className="mb-4 leading-7" {...props}>
        {children}
      </p>
    ),

    // 列表渲染
    ul: ({ children, ...props }: any) => (
      <ul className="mb-4 ml-6 list-disc space-y-1" {...props}>
        {children}
      </ul>
    ),
    ol: ({ children, ...props }: any) => (
      <ol className="mb-4 ml-6 list-decimal space-y-1" {...props}>
        {children}
      </ol>
    ),
    li: ({ children, ...props }: any) => (
      <li className="text-sm leading-6" {...props}>
        {children}
      </li>
    ),

    // 引用块渲染
    blockquote: ({ children, ...props }: any) => (
      <blockquote
        className="mb-4 pl-4 border-l-4 border-indigo-500 bg-gray-50 dark:bg-gray-800/50 py-2 italic"
        {...props}
      >
        {children}
      </blockquote>
    ),

    // 水平线渲染
    hr: (props: any) => (
      <hr className="my-6 border-t border-gray-200 dark:border-gray-700" {...props} />
    ),

    // 表格渲染
    table: ({ children, ...props }: any) => (
      <div className="mb-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 border border-gray-200 dark:border-gray-700" {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }: any) => (
      <thead className="bg-gray-50 dark:bg-gray-800" {...props}>
        {children}
      </thead>
    ),
    tbody: ({ children, ...props }: any) => (
      <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700" {...props}>
        {children}
      </tbody>
    ),
    tr: ({ children, ...props }: any) => (
      <tr className="hover:bg-gray-50 dark:hover:bg-gray-800" {...props}>
        {children}
      </tr>
    ),
    th: ({ children, ...props }: any) => (
      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: any) => (
      <td className="px-4 py-2 text-sm text-gray-900 dark:text-white" {...props}>
        {children}
      </td>
    ),

    // 任务列表渲染
    input: ({ checked, ...props }: any) => (
      <input
        type="checkbox"
        checked={checked}
        readOnly
        className={cn(
          'w-4 h-4 mr-2 rounded border-gray-300',
          'text-indigo-600 focus:ring-indigo-500',
          'cursor-not-allowed',
        )}
        {...props}
      />
    ),

    // 链接渲染
    a: ({ children, href, ...props }: any) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-indigo-600 dark:text-indigo-400 hover:underline"
        {...props}
      >
        {children}
      </a>
    ),

    // 图片渲染
    img: ({ src, alt, ...props }: any) => (
      <img
        src={src}
        alt={alt}
        className="max-w-full h-auto rounded-lg my-4"
        loading="lazy"
        {...props}
      />
    ),

    // 强调渲染
    strong: ({ children, ...props }: any) => (
      <strong className="font-semibold" {...props}>
        {children}
      </strong>
    ),
    em: ({ children, ...props }: any) => (
      <em className="italic" {...props}>
        {children}
      </em>
    ),
  };

  return (
    <div className={cn('prose prose-sm dark:prose-invert max-w-none', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}
        rehypePlugins={[rehypeKatex, rehypeRaw]}
        components={components}
      >
        {processedContent}
      </ReactMarkdown>
      {/* 流式渲染光标 */}
      {isStreaming && (
        <span className="inline-block w-0.5 h-4 bg-indigo-500 dark:bg-indigo-400 animate-pulse ml-1 align-middle" />
      )}
    </div>
  );
};

/**
 * 复制按钮组件
 */
interface CopyButtonProps {
  content: string;
}

const CopyButton: React.FC<CopyButtonProps> = ({ content }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={cn(
        'px-2 py-1 rounded text-xs font-medium transition-colors',
        'bg-gray-700 hover:bg-gray-600',
        'text-gray-300 hover:text-white',
        'opacity-0 group-hover:opacity-100',
        copied && 'bg-green-600 text-white',
      )}
      title={copied ? '已复制!' : '复制代码'}
    >
      {copied ? '✓' : '复制'}
    </button>
  );
};

export default MarkdownRenderer;
