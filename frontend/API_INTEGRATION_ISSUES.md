# Frontend API Integration Issues Report

## Executive Summary

The frontend chat message streaming functionality has **critical integration issues** that prevent it from working correctly. The main problem is a fundamental architectural mismatch between the frontend's use of EventSource (GET-only) and the backend's POST endpoint.

---

## Critical Issues

### 🔴 Issue #1: HTTP Method Mismatch (BLOCKING)

**Location**: [frontend/src/pages/chat/hooks/useChatActions.ts:171](frontend/src/pages/chat/hooks/useChatActions.ts#L171)

**Problem**:
```typescript
// Frontend uses EventSource (GET only)
const eventSource = new EventSource(url);
```

```python
# Backend expects POST
@chatMessageController.post('/stream')
async def send_message_stream(...):
```

**Impact**: ❌ **BLOCKING** - EventSource API only supports GET requests, but the backend endpoint is configured as POST.

**Evidence**:
- Backend: [chat_message_controller.py:32-34](backend/module_chat/controller/chat_message_controller.py#L32-L34)
- Frontend: [useChatActions.ts:171-172](frontend/src/pages/chat/hooks/useChatActions.ts#L171-L172)

---

### 🔴 Issue #2: Parameter Encoding Error (BLOCKING)

**Location**: [frontend/src/pages/chat/services/chatApi.ts:190-201](frontend/src/pages/chat/services/chatApi.ts#L190-L201)

**Problem**:
```typescript
export const getStreamMessageUrl = (
  conversationId: number,
  data: SendMessageRequest,
) => {
  const params = new URLSearchParams();
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined) {
      params.append(key, JSON.stringify(value));  // ❌ WRONG!
    }
  });
  return `/api/chat/messages/stream?${params.toString()}`;
};
```

**Generated URL Example**:
```
/api/chat/messages/stream?conversationId="123"&content="hello"&modelId="deepseek-chat"
```

**Issues**:
1. ❌ `JSON.stringify()` wraps values in extra quotes: `"123"` instead of `123`
2. ❌ `JSON.stringify()` on arrays creates malformed URLs: `attachments="[1,2,3]"`
3. ❌ Backend expects POST body, not query parameters

**Backend Expects**:
```python
class SendMessageModel(BaseModel):
    conversation_id: int        # From POST body
    content: str                # From POST body
    model_id: Optional[str]     # From POST body
    enable_search: Optional[bool]
    attachments: Optional[List[int]]
    temperature: Optional[float]
    max_tokens: Optional[int]
```

---

### 🟡 Issue #3: Missing Request Body

**Problem**: Backend expects `SendMessageModel` in request body (Pydantic model), but frontend sends nothing in body (only query string via GET).

**Backend Code**:
```python
async def send_message_stream(
    request: Request,
    send_message: SendMessageModel,  # ❌ Expects POST body
    ...
):
```

**Frontend Behavior**: EventSource sends GET request with no body, only URL query parameters.

---

## Detailed Analysis by Component

### 1. API Service Layer ([chatApi.ts](frontend/src/pages/chat/services/chatApi.ts))

**Status**: ❌ **NEEDS MAJOR REFACTOR**

**Issues**:
- All API endpoints correctly use `/api/chat/` prefix ✅
- HTTP response handling is correct (`res.code`, `res.data`) ✅
- `getStreamMessageUrl()` function is fundamentally broken ❌

**Required Changes**:
1. Remove `getStreamMessageUrl()` entirely (cannot use EventSource with POST)
2. Implement streaming with `fetch()` + `ReadableStream` or use a library
3. Properly serialize request body for POST requests

---

### 2. Chat Actions Hook ([useChatActions.ts](frontend/src/pages/chat/hooks/useChatActions.ts))

**Status**: ❌ **NEEDS MAJOR REFACTOR**

**Issues**:
- `sendMessage()` uses EventSource (lines 171-172) ❌
- SSE event handling logic is correct (lines 183-248) ✅
- Response data access uses correct pattern (`res.code` not `res.data.code`) ✅

**Required Changes**:
1. Replace EventSource with fetch() + ReadableStream for POST support
2. Manually parse SSE events from the response stream
3. Keep existing event handling logic (it's good)

---

### 3. Chat Area Component ([ChatArea.tsx](frontend/src/pages/chat/components/ChatArea.tsx))

**Status**: ✅ **CORRECT**

**Analysis**:
- Auto-creates conversation if none exists (lines 48-64) ✅
- Message sending flow is correct (lines 47-68) ✅
- Properly passes parameters to `sendMessage()` ✅

**No changes needed** - this component will work once the hook is fixed.

---

### 4. HTTP Interceptor ([http.ts](frontend/src/common/utils/http.ts))

**Status**: ✅ **CORRECT**

**Analysis**:
- Returns `res.data` directly (line 29) ✅
- Properly handles authentication headers ✅
- Error handling is correct ✅

**No changes needed**.

---

### 5. Vite Proxy Configuration ([vite.config.ts](frontend/vite.config.ts))

**Status**: ✅ **CORRECT**

**Analysis**:
- `/dev-api` proxy correctly configured ✅
- Rewrites path correctly (removes `/dev-api` prefix) ✅
- CORS handled via `changeOrigin: true` ✅

**No changes needed**.

---

## SSE Event Format Verification

**Backend SSE Events** ([chat_message_controller.py:67-110](backend/module_chat/controller/chat_message_controller.py#L67-L110)):
```python
yield f"event: message_start\ndata: {json.dumps({'messageId': user_message_id})}\n\n"
yield f"event: thinking_start\ndata: {json.dumps({})}\n\n"
yield f"event: thinking_delta\ndata: {json.dumps({'content': ...})}\n\n"
yield f"event: content_delta\ndata: {json.dumps({'content': ...})}\n\n"
yield f"event: message_end\ndata: {json.dumps({**event_data})}\n\n"
```

**Frontend SSE Handler** ([useChatActions.ts:183-248](frontend/src/pages/chat/hooks/useChatActions.ts#L183-L248)):
```typescript
switch (event.type) {
  case 'message_start': /* ✅ */
  case 'content_delta': /* ✅ */
  case 'thinking_start': /* ✅ */
  case 'thinking_delta': /* ✅ */
  case 'thinking_end': /* ✅ */
  case 'message_end': /* ✅ */
  case 'error': /* ✅ */
}
```

**Status**: ✅ **MATCHING** - SSE event formats are compatible.

---

## Solutions

### Option 1: Change Backend to GET (Recommended - Quick Fix)

**Pros**:
- Minimal frontend changes
- Can keep using EventSource
- Simpler implementation

**Cons**:
- GET requests have size limits (URL length)
- Less RESTful (sending data via GET)
- Query parameters visible in logs

**Changes Required**:
1. Backend: Change `@chatMessageController.post('/stream')` to `@chatMessageController.get('/stream')`
2. Backend: Change parameter from `send_message: SendMessageModel` to individual query parameters
3. Frontend: Fix parameter encoding (remove `JSON.stringify()`)

---

### Option 2: Change Frontend to fetch() + ReadableStream (Recommended - Proper)

**Pros**:
- RESTful API design (POST for data modification)
- No URL size limits
- More flexible and maintainable

**Cons**:
- More complex frontend implementation
- Cannot use EventSource API

**Changes Required**:
1. Frontend: Replace EventSource with `fetch()` + `ReadableStream`
2. Frontend: Manually parse SSE events from response stream
3. Frontend: Send POST body with proper JSON

---

## Recommended Implementation Plan

### Phase 1: Quick Fix (Option 1)
- Change backend endpoint to GET
- Fix frontend parameter encoding
- Test end-to-end

### Phase 2: Proper Solution (Option 2)
- Refactor frontend to use fetch() + ReadableStream
- Change backend back to POST
- Implement proper SSE parsing
- Add error handling and reconnection logic

---

## Testing Checklist

Before deployment, verify:
- [ ] Message sends successfully
- [ ] Streaming response displays in real-time
- [ ] Thinking content shows (for Reasoner model)
- [ ] Message completion triggers `message_end` event
- [ ] Errors are properly handled
- [ ] Conversation auto-creation works
- [ ] Message history loads correctly
- [ ] Re-generate functionality works

---

## All Other API Calls (Verified ✅)

| Endpoint | Frontend | Backend | Status |
|----------|----------|---------|--------|
| GET /api/chat/models | ✅ | ✅ | ✅ Correct |
| GET /api/chat/model-config | ✅ | ✅ | ✅ Correct |
| POST /api/chat/model-config | ✅ | ✅ | ✅ Correct |
| GET /api/chat/model-presets | ✅ | ✅ | ✅ Correct |
| GET /api/chat/conversations | ✅ | ✅ | ✅ Correct |
| GET /api/chat/conversations/:id | ✅ | ✅ | ✅ Correct |
| POST /api/chat/conversations | ✅ | ✅ | ✅ Correct |
| PUT /api/chat/conversations | ✅ | ✅ | ✅ Correct |
| DELETE /api/chat/conversations/:ids | ✅ | ✅ | ✅ Correct |
| PUT /api/chat/conversations/:id/pin | ✅ | ✅ | ✅ Correct |
| GET /api/chat/conversations/:id/export | ✅ | ✅ | ✅ Correct |
| GET /api/chat/conversations/:id/context | ✅ | ✅ | ✅ Correct |
| GET /api/chat/tags | ✅ | ✅ | ✅ Correct |
| POST /api/chat/tags | ✅ | ✅ | ✅ Correct |
| DELETE /api/chat/tags/:ids | ✅ | ✅ | ✅ Correct |
| GET /api/chat/conversations/:id/messages | ✅ | ✅ | ✅ Correct |
| **POST /api/chat/messages/stream** | ❌ | ✅ | ❌ **BROKEN** |
| POST /api/chat/messages/:id/stop | ✅ | ✅ | ✅ Correct |
| **POST /api/chat/messages/:id/regenerate** | ❌ | ✅ | ❌ **BROKEN** |
| POST /api/chat/files/upload | ✅ | ✅ | ✅ Correct |
| GET /api/chat/files | ✅ | ✅ | ✅ Correct |
| DELETE /api/chat/files/:ids | ✅ | ✅ | ✅ Correct |
| GET /api/chat/settings | ✅ | ✅ | ✅ Correct |
| PUT /api/chat/settings | ✅ | ✅ | ✅ Correct |

**Summary**: 20/22 endpoints are correct. Only 2 streaming endpoints are broken.

---

## Conclusion

The frontend has **critical issues** with the streaming message functionality that prevent it from working. The non-streaming API calls are all correct and working properly.

**Priority**: 🔴 **CRITICAL** - Streaming is the core feature of the chat module and is completely broken.

**Estimated Fix Time**:
- Option 1 (GET method): 1-2 hours
- Option 2 (fetch + stream): 3-4 hours
