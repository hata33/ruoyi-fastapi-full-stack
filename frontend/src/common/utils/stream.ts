/**
 * 流式请求工具函数
 * 用于处理 SSE (Server-Sent Events) 流式响应
 */

import { getStorage } from './index';

/**
 * 流式请求配置
 */
export interface StreamRequestOptions<T = { type: string; data: any }> {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: any;
  headers?: Record<string, string>;
  onEvent: (event: T) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

/**
 * 解析 SSE 行
 * SSE 格式: event: eventType\ndata: {"key":"value"}\n\n
 */
function parseSSELine(
  line: string,
  eventType: string,
  dataBuffer: string
): { eventType: string; dataBuffer: string; event: { type: string; data: any } | null } {
  // 空行表示事件结束
  if (line === '') {
    if (dataBuffer) {
      try {
        const eventData = JSON.parse(dataBuffer);
        return {
          eventType: '',
          dataBuffer: '',
          event: { type: eventType, data: eventData }
        };
      } catch (e) {
        console.error('Failed to parse SSE data:', dataBuffer, e);
        return { eventType, dataBuffer: '', event: null };
      }
    }
    return { eventType, dataBuffer, event: null };
  }

  // 解析 event: 行
  if (line.startsWith('event:')) {
    const newEventType = line.slice(6).trim();
    return {
      eventType: newEventType,
      dataBuffer,
      event: null
    };
  }

  // 解析 data: 行
  if (line.startsWith('data:')) {
    const newData = line.slice(5).trim();
    const newDataBuffer = dataBuffer ? (dataBuffer + newData) : newData;
    return {
      eventType,
      dataBuffer: newDataBuffer,
      event: null
    };
  }

  // 忽略其他行（如注释等）
  return { eventType, dataBuffer, event: null };
}

/**
 * 发起流式请求并处理 SSE 事件
 *
 * @param options - 流式请求配置
 * @returns 取消请求的函数
 */
export function streamRequest<T = { type: string; data: any }>(options: StreamRequestOptions<T>): () => void {
  const {
    url,
    method = 'POST',
    body,
    headers = {},
    onEvent,
    onError,
    onComplete
  } = options;

  // 添加认证头
  const authHeaders: Record<string, string> = {
    ...headers,
    'Authorization': `Bearer ${getStorage('token') || ''}`,
  };

  // 如果是 POST/PUT 且有 body，设置 Content-Type
  if ((method === 'POST' || method === 'PUT') && body) {
    authHeaders['Content-Type'] = 'application/json';
  }

  let abortController: AbortController | null = new AbortController();
  let isComplete = false;

  // 执行请求
  fetch(url, {
    method,
    headers: authHeaders,
    body: (method === 'POST' || method === 'PUT') && body ? JSON.stringify(body) : undefined,
    signal: abortController.signal
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // 读取流
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let eventType = '';
      let dataBuffer = '';

      try {
        while (!isComplete) {
          const { done, value } = await reader.read();

          if (done) {
            // 处理缓冲区中剩余的数据
            if (dataBuffer) {
              const event = parseSSELine('', eventType, dataBuffer).event;
              if (event) onEvent(event as T);
            }
            break;
          }

          // 解码并添加到缓冲区
          buffer += decoder.decode(value, { stream: true });

          // 按行处理
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 保留最后一个不完整的行

          for (const line of lines) {
            const result = parseSSELine(line.trim(), eventType, dataBuffer);
            eventType = result.eventType;
            dataBuffer = result.dataBuffer;

            if (result.event) {
              onEvent(result.event as T);

              // 检查是否是结束事件
              if (result.event.type === 'message_end' || result.event.type === 'error') {
                isComplete = true;
                break;
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
        if (!isComplete) {
          isComplete = true;
        }
      }
    })
    .catch((error) => {
      if (error.name === 'AbortError') {
        // 用户主动取消，不是错误
        console.log('Stream request was cancelled');
      } else {
        console.error('Stream request error:', error);
        onError?.(error);
      }
    })
    .finally(() => {
      if (isComplete) {
        onComplete?.();
      }
    });

  // 返回取消函数
  return () => {
    if (!isComplete) {
      isComplete = true;
      abortController?.abort();
      abortController = null;
    }
  };
}
