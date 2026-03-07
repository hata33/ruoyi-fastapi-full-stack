/**
 * Model Selector Component - 新拟物风格
 * 模型选择器组件
 */

import React, { useState, useRef, useEffect } from 'react';
import { DownOutlined, CheckOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useModels } from '../hooks/useChatActions';
import type { Model } from '../types';

const ModelSelector: React.FC = () => {
  const { models, currentModelId, setCurrentModel } = useModels();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentModel = models.find((m) => m.modelCode === currentModelId);

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectModel = (model: Model) => {
    setCurrentModel(model.modelCode);
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center space-x-2 px-3 py-2',
          'chat2-neu-btn',
          'min-w-[160px]',
          'chat2-text-primary',
        )}
      >
        <div className="flex items-center space-x-2 flex-1">
          {/* Model Icon */}
          <div className={cn(
            'w-6 h-6 rounded-lg',
            'chat2-neu-btn',
            'flex items-center justify-center',
            'bg-gradient-to-br from-indigo-500 to-purple-600',
          )}>
            <span className="text-white text-xs font-medium">AI</span>
          </div>
          {/* Model Name */}
          <span className="truncate font-medium text-sm">
            {currentModel?.modelName || '选择模型'}
          </span>
        </div>
        {/* Arrow */}
        <DownOutlined
          className={cn(
            'text-xs transition-transform duration-200',
            'chat2-text-secondary opacity-70',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={cn(
            'absolute top-full right-0 mt-2',
            'chat2-neu-card',
            'py-2',
            'min-w-[240px]',
            'z-50',
            'chat2-animate-fade-in',
          )}
        >
          {models.map((model, index) => (
            <button
              key={model.modelId}
              onClick={() => handleSelectModel(model)}
              className={cn(
                'w-full flex items-center justify-between px-4 py-2.5',
                'transition-all duration-200',
                index === 0 && 'rounded-t-xl',
                index === models.length - 1 && 'rounded-b-xl',
                'hover:bg-soft-accent/10',
              )}
            >
              <div className="flex items-center space-x-3 flex-1">
                {/* Model Icon */}
                <div
                  className={cn(
                    'w-8 h-8 rounded-lg',
                    'chat2-neu-btn',
                    'flex items-center justify-center',
                    model.modelType === 'reasoner'
                      ? 'bg-gradient-to-br from-orange-500 to-red-600'
                      : 'bg-gradient-to-br from-indigo-500 to-purple-600',
                  )}
                >
                  <span className="text-white text-xs font-medium">AI</span>
                </div>
                {/* Model Info */}
                <div className="text-left flex-1">
                  <div className={cn(
                    'font-medium truncate text-sm',
                    'chat2-text-primary',
                  )}>{model.modelName}</div>
                  <div className={cn(
                    'text-xs truncate',
                    'chat2-text-secondary opacity-70',
                  )}>
                    {model.modelType === 'reasoner' ? '深度推理' : '标准对话'}
                  </div>
                </div>
              </div>
              {/* Check Icon */}
              {model.modelCode === currentModelId && (
                <CheckOutlined className={cn(
                  'text-xs ml-2',
                  'text-soft-accent',
                )} />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
