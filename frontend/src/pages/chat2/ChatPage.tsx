/**
 * Chat2 Page Component - 新拟物风格
 * 聊天页面主组件
 */

import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MenuOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useChatStore } from './store/chatStore';
import * as chatApi from './services/chatApi';
import { useConversations, useChatUI } from './hooks/useChatActions';
import ChatHeader from './components/ChatHeader';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import './chat2.css';

const ChatPage: React.FC = () => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const { setCurrentConversation } = useConversations();
  const { sidebarVisible, toggleSidebar, setSidebarVisible } = useChatUI();

  // Zustand store 初始化
  const setModels = useChatStore((state) => state.setModels);
  const setCurrentModel = useChatStore((state) => state.setCurrentModel);

  // 初始化：加载模型列表
  useEffect(() => {
    const initializeModels = async () => {
      try {
        const modelsRes = await chatApi.fetchModels(true);
        if (modelsRes.code === 200 && modelsRes.data) {
          setModels(modelsRes.data);
          if (modelsRes.data.length > 0) {
            setCurrentModel(modelsRes.data[0].modelCode);
          } else {
            // 如果没有启用的模型，设置默认模型
            setCurrentModel('deepseek-chat');
          }
        } else {
          // 没有数据时设置默认模型
          setCurrentModel('deepseek-chat');
        }
      } catch (error) {
        console.error('Failed to initialize models:', error);
        // 加载失败时设置默认模型
        setCurrentModel('deepseek-chat');
      }
    };

    initializeModels();
  }, [setModels, setCurrentModel]);

  // 处理路由参数变化
  useEffect(() => {
    if (conversationId) {
      const id = parseInt(conversationId);
      if (!isNaN(id)) {
        setCurrentConversation(String(id));
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
    <div className="flex flex-col h-screen chat2-neu-bg dark:chat2-neu-bg">
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
              'w-10 h-10',
              'chat2-icon-btn',
              'text-soft-text dark:text-soft-text-dark',
            )}
          >
            <MenuOutlined />
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
            className="fixed inset-0 top-14 bg-black/30 backdrop-blur-sm z-30"
            onClick={() => setSidebarVisible(false)}
          />
        )}

        {/* Chat Area */}
        <ChatArea className="flex-1" />
      </div>
    </div>
  );
};

export default ChatPage;
