/**
 * Markdown Renderer Component - 新拟物风格
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
          <div className={cn(
            'flex items-center justify-between px-4 py-2 rounded-t-xl',
            'chat2-neu-card',
            'border-b border-soft-text/10',
          )}>
            <span className={cn(
              'text-xs font-mono',
              'chat2-text-secondary',
            )}>{language}</span>
            <CopyButton content={String(children).replace(/\n$/, '')} />
          </div>
          {/* 代码内容 */}
          <SyntaxHighlighter
            style={vscDarkPlus}
            language={language}
            PreTag="div"
            className="!bg-gray-900 !p-4 !text-xs rounded-b-xl !m-0"
            {...props}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code
          className={cn(
            'px-1.5 py-0.5 rounded-lg',
            'chat2-neu-inset-sm',
            'text-xs font-mono',
            'chat2-text-primary',
          )}
          {...props}
        >
          {children}
        </code>
      );
    },

    // 标题渲染
    h1: ({ children, ...props }: any) => (
      <h1 className={cn(
        'text-2xl font-bold mb-4 mt-6 pb-2',
        'border-b border-soft-text/20',
        'chat2-text-primary',
      )} {...props}>
        {children}
      </h1>
    ),
    h2: ({ children, ...props }: any) => (
      <h2 className={cn(
        'text-xl font-bold mb-3 mt-5',
        'chat2-text-primary',
      )} {...props}>
        {children}
      </h2>
    ),
    h3: ({ children, ...props }: any) => (
      <h3 className={cn(
        'text-lg font-semibold mb-2 mt-4',
        'chat2-text-primary',
      )} {...props}>
        {children}
      </h3>
    ),

    // 段落渲染
    p: ({ children, ...props }: any) => (
      <p className={cn(
        'mb-4 leading-7',
        'chat2-text-primary',
      )} {...props}>
        {children}
      </p>
    ),

    // 列表渲染
    ul: ({ children, ...props }: any) => (
      <ul className={cn(
        'mb-4 ml-6 list-disc space-y-1',
        'chat2-text-primary',
      )} {...props}>
        {children}
      </ul>
    ),
    ol: ({ children, ...props }: any) => (
      <ol className={cn(
        'mb-4 ml-6 list-decimal space-y-1',
        'chat2-text-primary',
      )} {...props}>
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
        className={cn(
          'mb-4 pl-4 py-2 italic rounded-xl',
          'border-l-4 border-soft-accent',
          'chat2-ai-message',
          'chat2-text-primary',
        )}
        {...props}
      >
        {children}
      </blockquote>
    ),

    // 水平线渲染
    hr: (props: any) => (
      <hr className={cn(
        'my-6',
        'border-t border-soft-text/20',
      )} {...props} />
    ),

    // 表格渲染
    table: ({ children, ...props }: any) => (
      <div className="mb-4 overflow-x-auto">
        <table className={cn(
          'min-w-full divide-y divide-soft-text/10',
          'border border-soft-text/10',
          'chat2-neu-card',
        )} {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }: any) => (
      <thead className={cn(
        'chat2-neu-inset-sm',
      )} {...props}>
        {children}
      </thead>
    ),
    tbody: ({ children, ...props }: any) => (
      <tbody className={cn(
        'divide-y divide-soft-text/10',
        'chat2-text-primary',
      )} {...props}>
        {children}
      </tbody>
    ),
    tr: ({ children, ...props }: any) => (
      <tr className={cn(
        'hover:bg-soft-accent/5',
        'transition-colors duration-150',
      )} {...props}>
        {children}
      </tr>
    ),
    th: ({ children, ...props }: any) => (
      <th className={cn(
        'px-4 py-2 text-left text-xs font-medium uppercase tracking-wider',
        'chat2-text-secondary',
      )} {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: any) => (
      <td className={cn(
        'px-4 py-2 text-sm',
        'chat2-text-primary',
      )} {...props}>
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
          'w-4 h-4 mr-2 rounded',
          'chat2-neu-inset-sm',
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
        className={cn(
          'text-soft-accent hover:text-soft-accent-hover',
          'hover:underline',
          'transition-colors duration-150',
        )}
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
        className="max-w-full h-auto rounded-2xl my-4 chat2-neu-card"
        loading="lazy"
        {...props}
      />
    ),

    // 强调渲染
    strong: ({ children, ...props }: any) => (
      <strong className={cn(
        'font-semibold',
        'chat2-text-primary',
      )} {...props}>
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
        <span className={cn(
          'inline-block w-0.5 h-4 animate-pulse ml-1 align-middle',
          'bg-soft-accent',
        )} />
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
        'px-2 py-1 rounded-lg text-xs font-medium transition-all duration-200',
        'chat2-neu-btn',
        'opacity-0 group-hover:opacity-100',
        copied && 'bg-soft-accent text-white',
        !copied && 'chat2-text-secondary',
      )}
      title={copied ? '已复制!' : '复制代码'}
    >
      {copied ? '✓' : '复制'}
    </button>
  );
};

export default MarkdownRenderer;
