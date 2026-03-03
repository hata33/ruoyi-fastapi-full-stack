/**
 * Chat Page Component
 * 聊天页面主组件
 */

import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MenuOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { ChatProvider } from './context/ChatContext';
import { useConversations, useChatUI } from './hooks/useChatActions';
import ChatHeader from './components/ChatHeader';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';

const ChatPageContent: React.FC = () => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const { fetchConversations, setCurrentConversation } = useConversations();
  const { sidebarVisible, toggleSidebar, setSidebarVisible } = useChatUI();

  // 初始化：加载会话列表
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // 处理路由参数变化
  useEffect(() => {
    if (conversationId) {
      const id = parseInt(conversationId);
      if (!isNaN(id)) {
        setCurrentConversation(id);
      }
    } else {
      // 如果没有 conversationId，可以选择创建新会话或加载最近会话
      // 这里我们暂时不做任何操作，让用户点击"新建对话"按钮
      setCurrentConversation(null);
    }
  }, [conversationId, setCurrentConversation]);

  // 判断是否为移动端
  const isMobile = window.innerWidth < 768;

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <ChatHeader />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Mobile Sidebar Toggle */}
        {isMobile && !sidebarVisible && (
          <button
            onClick={toggleSidebar}
            className={cn(
              'fixed top-16 left-4 z-50',
              'p-2 rounded-lg',
              'bg-white dark:bg-gray-800',
              'shadow-lg',
              'hover:bg-gray-100 dark:hover:bg-gray-700',
              'transition-colors duration-150',
            )}
          >
            <MenuOutlined className="text-gray-600 dark:text-gray-300" />
          </button>
        )}

        {/* Sidebar */}
        <div
          className={cn(
            'transition-all duration-300',
            isMobile && sidebarVisible && 'fixed inset-0 top-14 z-40',
          )}
        >
          <Sidebar
            className={cn(
              'h-full',
              isMobile && sidebarVisible && 'w-72',
            )}
          />
        </div>

        {/* Mobile Sidebar Overlay */}
        {isMobile && sidebarVisible && (
          <div
            className="fixed inset-0 top-14 bg-black/50 z-30"
            onClick={() => setSidebarVisible(false)}
          />
        )}

        {/* Chat Area */}
        <ChatArea className="flex-1" />
      </div>
    </div>
  );
};

const ChatPage: React.FC = () => {
  return (
    <ChatProvider>
      <ChatPageContent />
    </ChatProvider>
  );
};

export default ChatPage;
