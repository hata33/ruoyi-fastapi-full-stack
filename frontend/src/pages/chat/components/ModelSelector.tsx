/**
 * Model Selector Component
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
          'bg-gray-100 dark:bg-gray-700',
          'hover:bg-gray-200 dark:hover:bg-gray-600',
          'rounded-lg',
          'text-sm text-gray-900 dark:text-white',
          'transition-colors duration-150',
          'min-w-[160px]',
        )}
      >
        <div className="flex items-center space-x-2 flex-1">
          {/* Model Icon */}
          <div className="w-5 h-5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded flex items-center justify-center">
            <span className="text-white text-xs">AI</span>
          </div>
          {/* Model Name */}
          <span className="truncate font-medium">
            {currentModel?.modelName || '选择模型'}
          </span>
        </div>
        {/* Arrow */}
        <DownOutlined
          className={cn(
            'text-xs text-gray-500 dark:text-gray-400 transition-transform duration-200',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={cn(
            'absolute top-full right-0 mt-2',
            'bg-white dark:bg-gray-800',
            'border border-gray-200 dark:border-gray-700',
            'rounded-lg shadow-lg',
            'py-2',
            'min-w-[240px]',
            'z-50',
          )}
        >
          {models.map((model) => (
            <button
              key={model.modelId}
              onClick={() => handleSelectModel(model)}
              className={cn(
                'w-full flex items-center justify-between px-4 py-2',
                'hover:bg-gray-100 dark:hover:bg-gray-700',
                'text-sm text-gray-900 dark:text-white',
                'transition-colors duration-150',
                'first:rounded-t-lg last:rounded-b-lg',
              )}
            >
              <div className="flex items-center space-x-3 flex-1">
                {/* Model Icon */}
                <div
                  className={cn(
                    'w-8 h-8 rounded flex items-center justify-center',
                    model.modelType === 'reasoner'
                      ? 'bg-gradient-to-br from-orange-500 to-red-600'
                      : 'bg-gradient-to-br from-indigo-500 to-purple-600',
                  )}
                >
                  <span className="text-white text-xs">AI</span>
                </div>
                {/* Model Info */}
                <div className="text-left flex-1">
                  <div className="font-medium truncate">{model.modelName}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {model.modelType === 'reasoner' ? '深度推理' : '标准对话'}
                  </div>
                </div>
              </div>
              {/* Check Icon */}
              {model.modelCode === currentModelId && (
                <CheckOutlined className="text-indigo-500 text-xs ml-2" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
