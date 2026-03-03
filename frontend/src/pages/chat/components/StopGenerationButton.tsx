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
        'bg-red-50 dark:bg-red-900/20',
        'hover:bg-red-100 dark:hover:bg-red-900/30',
        'text-red-600 dark:text-red-400',
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
