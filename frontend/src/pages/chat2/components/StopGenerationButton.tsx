/**
 * Stop Generation Button Component - 新拟物风格
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
        'chat2-neu-btn',
        'text-sm font-medium',
        'chat2-text-primary',
        'hover:shadow-neu-inset-sm',
        'transition-all duration-200',
        className,
      )}
    >
      <CloseCircleOutlined className="text-base" />
      <span>停止生成</span>
    </button>
  );
};

export default StopGenerationButton;
