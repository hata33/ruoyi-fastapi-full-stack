/**
 * Stop Generation Button Component
 * 停止生成按钮组件
 */

import React from 'react';
import { CloseCircleOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';

interface StopGenerationButtonProps {
  onStop: () => void;
  className?: string;
}

const StopGenerationButton: React.FC<StopGenerationButtonProps> = ({ onStop, className }) => {
  return (
    <button
      onClick={onStop}
      className={cn(
        'flex items-center space-x-2 px-4 py-2',
        'bg-white dark:bg-gray-700',
        'hover:bg-gray-100 dark:hover:bg-gray-600',
        'text-gray-700 dark:text-gray-300',
        'border border-gray-300 dark:border-gray-600',
        'rounded-lg',
        'transition-all duration-200',
        'text-sm font-medium',
        className,
      )}
    >
      <CloseCircleOutlined className="text-base" />
      <span>停止生成</span>
    </button>
  );
};

export default StopGenerationButton;
