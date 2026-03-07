/**
 * Chat2 Sidebar Component - 新拟物风格
 * 聊天侧边栏组件
 */

import React, { useEffect, useCallback } from 'react';
import { PlusOutlined, PushpinOutlined, TagOutlined, BarChartOutlined } from '@ant-design/icons';
import { cn } from '@/utils/cn';
import { useChatStore } from '../store/chatStore';
import { useConversations, useTags, useChatUI } from '../hooks/useChatActions';
import ConversationList from './ConversationList';
import TagList from './TagList';
import StatsPanel from './StatsPanel';

interface SidebarProps {
  className?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const conversations = useChatStore((state) => state.conversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const sidebarCollapsed = useChatStore((state) => state.sidebarCollapsed);
  const sidebarVisible = useChatStore((state) => state.sidebarVisible);

  const { fetchConversations, createConversation, setCurrentConversation } = useConversations();
  const { tags, fetchTags } = useTags();
  const { setSidebarVisible } = useChatUI();

  // 加载会话列表
  useEffect(() => {
    fetchConversations();
    fetchTags();
  }, [fetchConversations, fetchTags]);

  // 新建会话
  const handleNewChat = useCallback(async () => {
    try {
      const newConversation = await createConversation({
        title: '新对话',
        modelId: 'deepseek-chat',
      });
      if (newConversation) {
        setCurrentConversation(newConversation.conversationId);
      }
    } catch (error: any) {
      console.error('Failed to create conversation:', error);
    }
  }, [createConversation, setCurrentConversation]);

  // 使用 useMemo 优化：计算统计数据和分组会话
  const { stats, pinnedConversations, unpinnedConversations } = React.useMemo(() => {
    // 按置顶和时间排序
    const sorted = [...conversations].sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return new Date(b.updateTime).getTime() - new Date(a.updateTime).getTime();
    });

    return {
      stats: {
        todayMessages: conversations.reduce((sum, c) => sum + c.messageCount, 0),
        totalTokens: conversations.reduce((sum, c) => sum + c.totalTokens, 0),
        totalConversations: conversations.length,
      },
      pinnedConversations: sorted.filter((c) => c.isPinned),
      unpinnedConversations: sorted.filter((c) => !c.isPinned),
    };
  }, [conversations]);

  // 移动端：点击后关闭侧边栏
  const handleConversationClick = useCallback((conversationId: string) => {
    setCurrentConversation(conversationId);
    if (window.innerWidth < 768) {
      setSidebarVisible(false);
    }
  }, [setCurrentConversation, setSidebarVisible]);

  if (!sidebarVisible) {
    return null;
  }

  return (
    <aside
      className={cn(
        'chat2-sidebar',
        'flex flex-col',
        sidebarCollapsed ? 'w-16' : 'w-72',
        'transition-all duration-300',
        className,
      )}
    >
      {/* New Chat Button */}
      <div className="px-4 py-3">
        <button
          onClick={handleNewChat}
          className={cn(
            'w-full flex items-center justify-center space-x-2',
            'chat2-neu-btn',
            'px-4 py-2.5',
            'font-medium text-sm',
            'chat2-text-primary',
          )}
        >
          <PlusOutlined className="text-base" />
          {!sidebarCollapsed && <span>新建对话</span>}
        </button>
      </div>

      {/* Conversation List */}
      {!sidebarCollapsed && (
        <div className="flex-1 overflow-y-auto px-3">
          {/* Pinned Conversations */}
          {pinnedConversations.length > 0 && (
            <>
              <div className="px-2 py-2">
                <div className={cn(
                  'flex items-center space-x-1.5 text-xs font-medium',
                  'chat2-text-secondary',
                )}>
                  <PushpinOutlined className="text-xs" />
                  <span>置顶</span>
                </div>
              </div>
              <ConversationList
                conversations={pinnedConversations}
                currentConversationId={currentConversationId}
                onConversationClick={handleConversationClick}
              />
            </>
          )}

          {/* Unpinned Conversations */}
          {unpinnedConversations.length > 0 && (
            <>
              {pinnedConversations.length > 0 && (
                <div className="px-2 py-2 mt-2">
                  <div className={cn(
                    'text-xs font-medium',
                    'chat2-text-secondary',
                  )}>
                    全部对话
                  </div>
                </div>
              )}
              <ConversationList
                conversations={unpinnedConversations}
                currentConversationId={currentConversationId}
                onConversationClick={handleConversationClick}
              />
            </>
          )}

          {/* Empty State */}
          {conversations.length === 0 && (
            <div className={cn(
              'flex flex-col items-center justify-center h-64',
              'chat2-text-secondary opacity-70',
            )}>
              <div className="text-4xl mb-2">💬</div>
              <div className="text-sm">暂无对话</div>
              <div className="text-xs mt-1">点击上方按钮开始新对话</div>
            </div>
          )}
        </div>
      )}

      {/* Bottom Section */}
      {!sidebarCollapsed && (
        <div className="px-3 pb-3">
          {/* Tags */}
          <div className="px-1 py-2">
            <button
              className={cn(
                'w-full flex items-center space-x-2',
                'px-3 py-2',
                'chat2-conversation-item',
                'text-sm chat2-text-primary',
              )}
            >
              <TagOutlined className="text-base" />
              <span className="flex-1 text-left">标签管理</span>
              {tags.length > 0 && (
                <span className={cn(
                  'text-xs',
                  'chat2-text-secondary opacity-60',
                )}>
                  {tags.length}
                </span>
              )}
            </button>
          </div>

          {/* Stats */}
          <div className="px-1 pb-2">
            <StatsPanel stats={stats} />
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
