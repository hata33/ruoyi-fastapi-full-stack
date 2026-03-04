/**
 * Input Area Component
 * 输入区域组件
 */

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { PaperClipOutlined, SendOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useChatContext } from '../context/ChatContext';
import { useMessages } from '../hooks/useChatActions';
import type { SendMessageRequest } from '../types';

interface InputAreaProps {
  onSendMessage?: (data: SendMessageRequest) => Promise<void>;
}

const InputArea: React.FC<InputAreaProps> = ({ onSendMessage: externalOnSendMessage }) => {
  const { currentConversationId, currentModelId } = useChatContext();
  const { sendMessage: defaultSendMessage } = useMessages();
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 使用外部传入的发送函数或默认的
  const sendMessage = externalOnSendMessage || defaultSendMessage;

  // 自动调整输入框高度
  // Note: Inline styles are necessary here for dynamic height calculation based on scrollHeight
  // This cannot be replaced with CSS classes as the value is computed at runtime
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  // 处理发送消息
  const handleSend = async () => {
    const content = inputValue.trim();
    if (!content) return;

    const messageData: SendMessageRequest = {
      conversationId: currentConversationId || 0, // 如果没有会话ID，会在 ChatArea 中自动创建
      content,
      modelId: currentModelId,
    };

    try {
      await sendMessage(messageData);
      setInputValue('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 处理文件上传
  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // TODO: Implement file upload
    console.log('File to upload:', file.name);
  };

  const canSend = inputValue.trim().length > 0;

  return (
    <div className="px-4 py-3">
      {/* Attachments */}
      {/* TODO: Add attachments display */}

      {/* Input Box */}
      <div
        className={cn(
          'flex items-end space-x-3',
          'bg-white dark:bg-gray-700',
          'rounded-xl px-4 py-3',
          'border border-gray-300 dark:border-gray-600 focus-within:border-gray-400 dark:focus-within:border-gray-500',
          'transition-all duration-200',
        )}
      >
        {/* Attachment Button */}
        <button
          onClick={handleFileUpload}
          className={cn(
            'flex-shrink-0 p-2 rounded-lg',
            'hover:bg-gray-200 dark:hover:bg-gray-600',
            'text-gray-500 dark:text-gray-400',
            'transition-colors duration-150',
          )}
          title="上传文件"
        >
          <PaperClipOutlined className="text-lg" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息... (Enter 发送，Shift + Enter 换行)"
          className={cn(
            'flex-1 resize-none',
            'bg-transparent',
            'text-gray-900 dark:text-white',
            'placeholder:text-gray-500 dark:placeholder:text-gray-400',
            'focus:outline-none',
            'min-h-[24px] max-h-[200px]',
            'text-base leading-relaxed',
          )}
          rows={1}
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!canSend}
          className={cn(
            'flex-shrink-0 p-2 rounded-lg',
            'bg-gray-900 dark:bg-white',
            'hover:bg-gray-800 dark:hover:bg-gray-100',
            'disabled:bg-gray-300 dark:disabled:bg-gray-600',
            'text-white dark:text-gray-900',
            'disabled:text-gray-500 dark:disabled:text-gray-400',
            'transition-colors duration-150',
            'disabled:cursor-not-allowed',
          )}
          title="发送消息 (Enter)"
        >
          <SendOutlined className={cn('text-lg', canSend ? 'rotate-[-45deg]' : '')} />
        </button>
      </div>

      {/* Hint */}
      <div className="flex items-center justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
        <span>AI 生成的内容可能不准确，请核实重要信息。</span>
        <span>{inputValue.length} / 4000</span>
      </div>
    </div>
  );
};

export default InputArea;
