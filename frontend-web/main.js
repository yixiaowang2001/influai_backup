// API配置
const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/updates';

// 用户帖子存储
let userPosts = [];

// 默认用户信息 - 将从后端获取
let currentUser = null;

// 应用状态枚举
const APP_STATES = {
  USER_SELECTION: 'user_selection',
  TEMPLATE_SELECTION: 'template_selection',
  MAIN_APP: 'main_app'
};

// 当前页面状态
let currentAppState = APP_STATES.USER_SELECTION;
let currentView = 'timeline'; // 'timeline' 或 'detail'
let currentPost = null;
let isCommentInputVisible = false; // 评论输入框是否显示
let currentSortOrder = 'time'; // 'time' 或 'likes'

// 用户管理相关状态
let availableUsers = [];
let availableTemplates = [];
let selectedUser = null;

// WebSocket连接
let websocket = null;

// ===== API调用函数 =====

// 通用API调用函数
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API调用失败:', endpoint, error);
    throw error;
  }
}

// 获取当前用户信息
async function getCurrentUser() {
  try {
    const response = await apiCall('/user/current');
    return response.data;
  } catch (error) {
    // 如果没有当前用户，返回null而不是抛出错误
    console.log('没有当前用户，需要进行用户选择');
    return null;
  }
}

// 获取所有用户
async function getAllUsers() {
  const response = await apiCall('/user/profile');
  return response.data;
}

// 设置当前用户
async function setCurrentUser(userId) {
  const response = await apiCall('/user/set-current', {
    method: 'POST',
    body: JSON.stringify({ human_user_id: userId })
  });
  return response.data;
}

// 获取帖子列表
async function fetchPosts() {
  const response = await apiCall('/posts');
  return response.data;
}

// 发布帖子
async function createPost(content) {
  const response = await apiCall('/posts', {
    method: 'POST',
    body: JSON.stringify({ content })
  });
  return response.data;
}

// 点赞帖子
async function likePost(postId) {
  const response = await apiCall(`/posts/${postId}/like`, {
    method: 'POST'
  });
  return response.data;
}

// 获取评论列表
async function fetchComments(postId, sort = 'time') {
  const response = await apiCall(`/posts/${postId}/comments?sort=${sort}`);
  return response.data;
}

// 发布评论
async function createComment(postId, content) {
  const response = await apiCall(`/posts/${postId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ content })
  });
  return response.data;
}

// 点赞评论
async function likeComment(commentId) {
  const response = await apiCall(`/comments/${commentId}/like`, {
    method: 'POST'
  });
  return response.data;
}

// 获取用户模板列表
async function getUserTemplates() {
  const response = await apiCall('/user-templates');
  return response.data;
}

// 创建新用户
async function createNewUser(username, templateId, avatarPath = '') {
  const response = await apiCall('/user/create', {
    method: 'POST',
    body: JSON.stringify({
      username: username,
      user_template_id: templateId,
      avatar_path: avatarPath
    })
  });
  return response.data;
}

// 注意：fetchPostsCommentsStats 函数已移除
// 因为后端现在直接在帖子列表API中返回正确的评论数

// ===== WebSocket函数 =====

// 初始化WebSocket连接
function initWebSocket() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    console.log('WebSocket已经连接，跳过重复连接');
    return;
  }
  
  if (websocket) {
    websocket.close();
  }
  
  websocket = new WebSocket(WS_URL);
  
  websocket.onopen = function(event) {
    // WebSocket连接已建立
  };
  
  websocket.onmessage = function(event) {
    try {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
    }
  };
  
  websocket.onclose = function(event) {
    websocket = null; // 清空websocket引用
    // 只有在主应用状态下才重连
    if (currentAppState === APP_STATES.MAIN_APP) {
      setTimeout(initWebSocket, 3000);
    }
  };
  
  websocket.onerror = function(error) {
    console.error('WebSocket错误:', error);
  };
}

// 处理WebSocket消息
function handleWebSocketMessage(message) {
  console.log('收到WebSocket消息:', message);
  
  switch (message.type) {
    case 'new_post':
      // 新帖子，添加到列表顶部
      userPosts.unshift(message.data);
      if (currentView === 'timeline') {
        renderPosts(userPosts);
      }
      break;
      
    case 'post_like_update':
      // 帖子点赞更新
      updatePostLikes(message.data.postId, message.data.likes, message.data.isLiked);
      break;
      
    case 'new_comment':
      // 新评论
      handleNewComment(message.data);
      break;
      
    case 'comment_like_update':
      // 评论点赞更新
      updateCommentLikes(message.data.commentId, message.data.likes, message.data.isLiked);
      break;
      
    case 'new_comment_push':
      // AI评论推送（每3-5秒一条）
      handleAICommentPush(message.data);
      break;
      
    case 'comment_push_complete':
      // 评论推送完成通知
      handleCommentPushComplete(message.data);
      break;
  }
}

// 更新帖子点赞数
function updatePostLikes(postId, likes, isLiked) {
  const post = userPosts.find(p => p.id === postId);
  if (post) {
    post.likes = likes;
    post.isLiked = isLiked;
    
    if (currentView === 'timeline') {
      renderPosts(userPosts);
    } else if (currentView === 'detail' && currentPost && currentPost.id === postId) {
      currentPost.likes = likes;
      currentPost.isLiked = isLiked;
      renderPostDetail(currentPost);
    }
  }
}

// 处理AI评论推送
function handleAICommentPush(data) {
  console.log('[DEBUG] handleAICommentPush 收到推送:', data.postId, '当前视图:', currentView);
  
  // 如果在详情页且是当前帖子的评论，直接添加评论到界面
  if (currentView === 'detail' && currentPost && currentPost.id === data.postId) {
    console.log('[DEBUG] 在详情页，添加评论到详情页');
    
    // 直接添加评论到当前帖子的评论列表
    if (!currentPost.comments) {
      currentPost.comments = [];
    }
    currentPost.comments.push(data.comment);
    
    // 重新渲染详情页
    renderPostDetail(currentPost);
  }
  
  // 更新帖子的评论数
  const post = userPosts.find(p => p.id === data.postId);
  if (post) {
    console.log('[DEBUG] 找到帖子，当前评论数:', post.commentsCount, '即将加1');
    // 评论数加1
    post.commentsCount = (post.commentsCount || 0) + 1;
    console.log('[DEBUG] 更新后评论数:', post.commentsCount);
    
    if (currentView === 'timeline') {
      console.log('[DEBUG] 在时间线视图，重新渲染帖子列表');
      renderPosts(userPosts);
    }
  } else {
    console.log('[DEBUG] 未找到对应帖子:', data.postId);
  }
}

// 处理评论推送完成通知
function handleCommentPushComplete(data) {
  console.log('评论推送完成:', data);
  
  // 可以在这里添加用户提示，比如显示"该帖子的所有评论已推送完毕"
  // 暂时只在控制台输出，后续可以添加UI提示
  
  // 如果在详情页，确保评论列表是最新的
  if (currentView === 'detail' && currentPost && currentPost.id === data.postId) {
    loadCommentsForCurrentPost();
  }
}

// 处理新评论
function handleNewComment(data) {
  if (currentView === 'detail' && currentPost && currentPost.id === data.postId) {
    // 如果在详情页且是当前帖子的评论，重新加载评论列表
    loadCommentsForCurrentPost();
  }
  
  // 更新帖子的评论数
  const post = userPosts.find(p => p.id === data.postId);
  if (post) {
    post.commentsCount = data.commentsCount;
    if (currentView === 'timeline') {
      renderPosts(userPosts);
    }
  }
}

// 更新评论点赞数
function updateCommentLikes(commentId, likes, isLiked) {
  if (currentView === 'detail' && currentPost) {
    // 重新渲染详情页以更新评论点赞状态
    loadCommentsForCurrentPost();
  }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', async () => {
  const commentInput = document.getElementById('postContent');
  const postButton = document.getElementById('postButton');
  const charCount = document.getElementById('charCount');
  const postsContainer = document.getElementById('postsContainer');
  
  // 初始化应用
  await initializeApp();
  
  // 输入框内容变化监听
  commentInput.addEventListener('input', () => {
    const text = commentInput.value;
    const count = text.length;
    
    // 更新字数显示
    charCount.textContent = count;
    charCount.className = count > 140 ? 'text-red-500 font-bold' : 'text-gray-500';
    
    // 更新按钮状态
    postButton.disabled = count === 0 || count > 140;
  });
  
  // 发送按钮点击事件
  postButton.addEventListener('click', async () => {
    const content = commentInput.value.trim();
    if (content.length === 0 || content.length > 140) return;
    
    // 禁用按钮防止重复提交
    postButton.disabled = true;
    postButton.textContent = '发送中...';
    
    try {
      // 调用API发布帖子
      const newPost = await createPost(content);
      
      // 清空输入框
      commentInput.value = '';
      charCount.textContent = '0';
      
      // 不需要手动添加到列表，WebSocket会推送更新
      console.log('帖子发布成功:', newPost);
      showSuccessMessage('帖子发布成功！');
    } catch (error) {
      console.error('发布失败:', error);
      showErrorMessage('发布失败，请重试');
    } finally {
      // 恢复按钮状态
      postButton.disabled = content.length === 0 || content.length > 140;
      postButton.textContent = '发布';
    }
  });
});

// 初始化应用
async function initializeApp() {
  try {
    console.log('[DEBUG] initializeApp 开始执行');
    
    // 显示加载状态
    console.log('[DEBUG] 显示加载状态');
    showLoadingState();
    
    // 并行获取所有初始化数据
    console.log('[DEBUG] 开始并行获取初始化数据');
    const [users, templates, existingUser] = await Promise.all([
      getAllUsers(),
      getUserTemplates(), 
      getCurrentUser()
    ]);
    console.log('[DEBUG] 初始化数据获取完成', { users: users?.length, templates: templates?.length, existingUser: !!existingUser });
    
    availableUsers = users;
    availableTemplates = templates;
    
    if (existingUser) {
      console.log('[DEBUG] 有现有用户，进入主应用流程');
      // 如果已有当前用户，直接进入主应用
      currentUser = existingUser;
      currentAppState = APP_STATES.MAIN_APP;
      currentView = 'timeline';
      togglePublishArea(true);
      
      // 加载帖子和初始化WebSocket
      console.log('[DEBUG] 开始加载帖子');
      await loadPosts();
      console.log('[DEBUG] 帖子加载完成，初始化WebSocket');
      initWebSocket();
      
      console.log('[DEBUG] 调用 renderCurrentState()');
      renderCurrentState();
      console.log('[DEBUG] renderCurrentState() 完成');
    } else {
      console.log('[DEBUG] 无现有用户，进入用户选择流程');
      // 没有当前用户，进入用户选择状态
      currentAppState = APP_STATES.USER_SELECTION;
      // 先渲染一次（可能显示加载状态）
      renderCurrentState();
      // 确保数据加载完成后再次渲染
      if (availableUsers.length > 0) {
        renderCurrentState();
      }
      togglePublishArea(false);
    }
    
    console.log('[DEBUG] initializeApp 执行完成');
  } catch (error) {
dui    console.error('[DEBUG] 应用初始化失败:', error);
    showErrorState(`应用初始化失败: ${error.message}`);
  }
}

// 加载帖子列表
async function loadPosts() {
  try {
    console.log('[DEBUG] loadPosts 开始执行');
    
    // 直接加载帖子数据（现在包含正确的评论数）
    console.log('[DEBUG] 调用 fetchPosts()');
    userPosts = await fetchPosts();
    console.log('[DEBUG] fetchPosts() 完成，获得帖子数量:', userPosts?.length);
    
    console.log('[DEBUG] 调用 renderPosts()');
    renderPosts(userPosts);  // 立即显示帖子，包含正确的评论数
    console.log('[DEBUG] renderPosts() 完成');
    
    // 注意：新发布的帖子的评论会通过WebSocket实时推送更新
    console.log('[DEBUG] loadPosts 执行完成');
  } catch (error) {
    console.error('[DEBUG] 加载帖子失败:', error);
    showErrorMessage('加载帖子失败');
  }
}

// 注意：loadCommentsStatsAsync 函数已移除
// 因为后端现在直接在帖子列表API中返回正确的评论数

// 显示加载状态
function showLoadingState() {
  const postsContainer = document.getElementById('postsContainer');
  postsContainer.innerHTML = `
    <div class="flex items-center justify-center py-8">
      <div class="text-gray-500">正在加载...</div>
    </div>
  `;
}

// 隐藏加载状态
function hideLoadingState() {
  // 由renderPosts处理
}

// 显示错误状态
function showErrorState(message) {
  const postsContainer = document.getElementById('postsContainer');
  postsContainer.innerHTML = `
    <div class="flex items-center justify-center py-8">
      <div class="text-red-500">${message}</div>
    </div>
  `;
}

// 显示错误消息
function showErrorMessage(message) {
  console.error(message);
  const errorElement = document.getElementById('errorMessage');
  const errorText = document.getElementById('errorText');
  errorText.textContent = message;
  errorElement.classList.remove('hidden');
  
  // 3秒后自动隐藏
  setTimeout(() => {
    hideErrorMessage();
  }, 3000);
}

// 隐藏错误消息
function hideErrorMessage() {
  const errorElement = document.getElementById('errorMessage');
  errorElement.classList.add('hidden');
}

// 显示成功消息
function showSuccessMessage(message) {
  console.log(message);
  const successElement = document.getElementById('successMessage');
  const successText = document.getElementById('successText');
  successText.textContent = message;
  successElement.classList.remove('hidden');
  
  // 2秒后自动隐藏
  setTimeout(() => {
    hideSuccessMessage();
  }, 2000);
}

// 隐藏成功消息
function hideSuccessMessage() {
  const successElement = document.getElementById('successMessage');
  successElement.classList.add('hidden');
}

// 控制发布框显示/隐藏
function togglePublishArea(show) {
  const publishArea = document.getElementById('publishArea');
  if (show) {
    publishArea.classList.remove('hidden');
  } else {
    publishArea.classList.add('hidden');
  }
}

// 排序评论 - 注意：现在排序在后端完成
function sortComments(comments, order) {
  // 后端已经排序，直接返回
  return comments;
}

// 切换排序方式
async function toggleSortOrder(newOrder) {
  currentSortOrder = newOrder;
  if (currentPost) {
    await loadCommentsForCurrentPost();
  }
}

// 渲染帖子详情（不包含评论）
function renderPostDetailWithoutComments(post) {
  const postsContainer = document.getElementById('postsContainer');
  
  const htmlContent = `
    <div class="post-detail">
      <!-- 返回按钮 -->
      <div class="p-4 border-b border-gray-200 bg-gray-50">
        <button onclick="backToTimeline()" class="text-gray-600 hover:text-gray-800 flex items-center">
          <i class="fas fa-arrow-left mr-2"></i>
          返回时间线
        </button>
      </div>
      
      <!-- 帖子内容 -->
      <div class="post-item">
        <div class="p-4 cursor-pointer" onclick="showCommentInput('${post.id}')">
          <div class="flex items-center mb-3">
            <div class="font-medium text-gray-900">${post.author?.username || post.username}</div>
            <span class="text-gray-500 text-sm ml-2">${post.author?.userId || post.userId}</span>
            <span class="text-gray-500 text-sm ml-auto">${post.timestamp}</span>
          </div>
          <p class="text-gray-800 leading-relaxed">${post.content}</p>
        </div>
        
        <!-- 帖子底部操作区 -->
        <div class="px-4 pb-3 flex justify-between items-center">
          <div class="text-black font-medium">评论</div>
          <div class="text-gray-700">
            赞 ${post.likes}
          </div>
        </div>
        
        <!-- 部分黑线效果 -->
        <div class="relative">
          <div class="border-b border-gray-200"></div>
          <div class="absolute left-4 bottom-0 w-8 border-b-2 border-black"></div>
        </div>
        
        <!-- 评论统计和筛选 -->
        <div class="px-4 py-3 bg-gray-50 flex justify-between items-center text-sm">
          <span class="text-gray-600"></span>
          <div class="relative">
            <button 
              id="sortDropdown" 
              onclick="toggleDropdown()" 
              class="text-gray-700 hover:text-gray-900 flex items-center cursor-pointer"
            >
              ${currentSortOrder === 'time' ? '按时间排序' : '按点赞排序'}
              <i class="fas fa-chevron-down ml-1 text-xs"></i>
            </button>
            <div id="dropdownMenu" class="dropdown-menu hidden">
              <div 
                class="dropdown-item ${currentSortOrder === 'time' ? 'selected' : ''}" 
                onclick="selectSort('time')"
              >
                按时间排序
              </div>
              <div 
                class="dropdown-item ${currentSortOrder === 'likes' ? 'selected' : ''}" 
                onclick="selectSort('likes')"
              >
                按点赞排序
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 评论列表占位 -->
      <div class="comments-list">
        <!-- 空白区域，等待评论加载或推送 -->
      </div>
    </div>
  `;
  
  postsContainer.innerHTML = htmlContent;
}

// 格式化时间戳
function formatTimestamp(date) {
  const now = new Date();
  const diff = now - date;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (seconds < 60) {
    return '刚刚';
  } else if (minutes < 60) {
    return `${minutes}分钟前`;
  } else if (hours < 24) {
    return `${hours}小时前`;
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    // 超过7天显示具体日期
    return date.toLocaleDateString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}

// 显示评论输入框
function showCommentInput(postId) {
  const post = userPosts.find(p => p.id === postId);
  if (!post || isCommentInputVisible) return;
  
  isCommentInputVisible = true;
  
  // 创建评论输入框 - 和发布框相同的大小和样式
  const commentInputHTML = `
    <div id="commentInputBox" class="comment-input-box">
      <div class="p-4 border-t border-gray-200 bg-white">
        <textarea 
          id="commentContent" 
          placeholder="写评论..." 
          class="w-full p-3 border border-gray-200 rounded focus:ring-1 focus:ring-gray-400 focus:border-gray-400 h-20 resize-none"
        ></textarea>
        <div class="flex justify-between items-center mt-2">
          <div class="text-sm text-gray-500">
            <span id="commentCharCount">0</span>/140
          </div>
          <div class="space-x-2">
            <button onclick="hideCommentInput()" class="px-3 py-1 text-sm text-gray-600 hover:text-gray-800">
              取消
            </button>
            <button 
              id="commentSubmitBtn" 
              onclick="submitComment(${postId})" 
              class="px-4 py-1 bg-black text-white rounded font-medium hover:bg-gray-800 transition disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              disabled
            >
              评论
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // 插入到页面底部
  document.body.insertAdjacentHTML('beforeend', commentInputHTML);
  
  // 添加事件监听
  const commentTextarea = document.getElementById('commentContent');
  const commentCharCount = document.getElementById('commentCharCount');
  const commentSubmitBtn = document.getElementById('commentSubmitBtn');
  
  commentTextarea.addEventListener('input', () => {
    const text = commentTextarea.value;
    const count = text.length;
    
    commentCharCount.textContent = count;
    commentCharCount.className = count > 140 ? 'text-red-500 font-bold' : 'text-gray-500';
    
    commentSubmitBtn.disabled = count === 0 || count > 140;
  });
  
  // 自动聚焦
  commentTextarea.focus();
}

// 隐藏评论输入框
function hideCommentInput() {
  const commentInputBox = document.getElementById('commentInputBox');
  if (commentInputBox) {
    commentInputBox.remove();
  }
  isCommentInputVisible = false;
}

// 提交评论
async function submitComment(postId) {
  const commentContent = document.getElementById('commentContent').value.trim();
  if (!commentContent || commentContent.length > 140) return;
  
  try {
    // 调用API发布评论
    const newComment = await createComment(postId, commentContent);
    console.log('评论发布成功:', newComment);
    
    // 隐藏输入框
    hideCommentInput();
    
    // WebSocket会推送更新，不需要手动更新UI
  } catch (error) {
    console.error('评论发布失败:', error);
    showErrorMessage('评论发布失败，请重试');
  }
}

// 点击帖子进入详情页
async function viewPostDetail(postId) {
  const post = userPosts.find(p => p.id === postId);
  if (post) {
    currentView = 'detail';
    currentPost = post;
    togglePublishArea(false); // 隐藏发布框
    
    // 确保WebSocket连接正常
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      initWebSocket();
    }
    
    // 显示帖子详情，但先不显示评论
    renderPostDetailWithoutComments(post);
    
    // 异步加载评论
    await loadCommentsForCurrentPost();
  }
}

// 为当前帖子加载评论
async function loadCommentsForCurrentPost() {
  if (!currentPost) return;
  
  try {
    const comments = await fetchComments(currentPost.id, currentSortOrder);
    currentPost.comments = comments;
    renderPostDetail(currentPost);
  } catch (error) {
    console.error('加载评论失败:', error);
    showErrorMessage('加载评论失败');
  }
}

// 返回时间线
function backToTimeline() {
  currentView = 'timeline';
  currentPost = null;
  hideCommentInput(); // 确保隐藏评论输入框
  togglePublishArea(true); // 显示发布框
  
  // 确保WebSocket连接正常
  if (!websocket || websocket.readyState !== WebSocket.OPEN) {
    initWebSocket();
  }
  
  renderPosts(userPosts);
}

// 渲染帖子列表
function renderPosts(posts) {
  console.log('[DEBUG] renderPosts 开始执行，帖子数量:', posts?.length);
  
  const postsContainer = document.getElementById('postsContainer');
  console.log('[DEBUG] 获取 postsContainer 元素:', !!postsContainer);
  
  if (!posts || posts.length === 0) {
    console.log('[DEBUG] 无帖子，显示空状态');
    postsContainer.innerHTML = `
      <div class="flex items-center justify-center py-8">
        <div class="text-gray-500">暂无帖子</div>
      </div>
    `;
    return;
  }
  
  // 生成帖子HTML - 使用扁平样式，细灰线分隔
  const htmlContent = posts.map(post => `
    <div class="post-item">
      <div class="p-4 cursor-pointer" onclick="viewPostDetail('${post.id}')">
        <div class="flex items-center mb-3">
          <div class="font-medium text-gray-900">${post.author?.username || post.username}</div>
          <span class="text-gray-500 text-sm ml-2">${post.author?.userId || post.userId}</span>
          <span class="text-gray-500 text-sm ml-auto">${post.timestamp}</span>
        </div>
        <p class="text-gray-800 leading-relaxed">${post.content}</p>
      </div>
      <div class="actions-bar">
        <button class="action-button comment-btn" onclick="event.stopPropagation(); showCommentInput('${post.id}')">
          <i class="far fa-comment"></i>
          ${post.commentsCount > 0 ? `<span class="ml-1 text-sm">${post.commentsCount}</span>` : ''}
        </button>
        <button class="action-button like-btn ${post.isLiked ? 'liked' : ''}" onclick="event.stopPropagation(); handleLike('${post.id}')">
          <i class="${post.isLiked ? 'fas' : 'far'} fa-heart"></i>
          ${post.likes > 0 ? `<span class="ml-1 text-sm">${post.likes}</span>` : ''}
        </button>
      </div>
    </div>
  `).join('');
  
  console.log('[DEBUG] 设置 postsContainer.innerHTML，HTML长度:', htmlContent.length);
  postsContainer.innerHTML = htmlContent;
  console.log('[DEBUG] renderPosts 执行完成');
}

// 渲染帖子详情页面
function renderPostDetail(post) {
  const postsContainer = document.getElementById('postsContainer');
  
  // 排序评论（后端已排序）
  const sortedComments = post.comments || [];
  
  const htmlContent = `
    <div class="post-detail">
      <!-- 返回按钮 -->
      <div class="p-4 border-b border-gray-200 bg-gray-50">
        <button onclick="backToTimeline()" class="text-gray-600 hover:text-gray-800 flex items-center">
          <i class="fas fa-arrow-left mr-2"></i>
          返回时间线
        </button>
      </div>
      
      <!-- 帖子内容 -->
      <div class="post-item">
        <div class="p-4 cursor-pointer" onclick="showCommentInput('${post.id}')">
          <div class="flex items-center mb-3">
            <div class="font-medium text-gray-900">${post.author?.username || post.username}</div>
            <span class="text-gray-500 text-sm ml-2">${post.author?.userId || post.userId}</span>
            <span class="text-gray-500 text-sm ml-auto">${post.timestamp}</span>
          </div>
          <p class="text-gray-800 leading-relaxed">${post.content}</p>
        </div>
        
        <!-- 帖子底部操作区 -->
        <div class="px-4 pb-3 flex justify-between items-center">
          <div class="text-black font-medium">评论</div>
          <div class="text-gray-700">
            赞 ${post.likes}
          </div>
        </div>
        
        <!-- 部分黑线效果 -->
        <div class="relative">
          <div class="border-b border-gray-200"></div>
          <div class="absolute left-4 bottom-0 w-8 border-b-2 border-black"></div>
        </div>
        
        <!-- 评论统计和筛选 -->
        <div class="px-4 py-3 bg-gray-50 flex justify-between items-center text-sm">
          <span class="text-gray-600">共 ${sortedComments.length} 条评论</span>
          <div class="relative">
            <button 
              id="sortDropdown" 
              onclick="toggleDropdown()" 
              class="text-gray-700 hover:text-gray-900 flex items-center cursor-pointer"
            >
              ${currentSortOrder === 'time' ? '按时间排序' : '按点赞排序'}
              <i class="fas fa-chevron-down ml-1 text-xs"></i>
            </button>
            <div id="dropdownMenu" class="dropdown-menu hidden">
              <div 
                class="dropdown-item ${currentSortOrder === 'time' ? 'selected' : ''}" 
                onclick="selectSort('time')"
              >
                按时间排序
              </div>
              <div 
                class="dropdown-item ${currentSortOrder === 'likes' ? 'selected' : ''}" 
                onclick="selectSort('likes')"
              >
                按点赞排序
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 评论列表 -->
      <div class="comments-list">
        ${sortedComments.map(comment => `
          <div class="comment-item border-b border-gray-200">
            <div class="p-4">
              <div class="flex items-center mb-3">
                <div class="font-medium text-gray-900">${comment.author?.username || comment.username}</div>
                <span class="text-gray-500 text-sm ml-2">${comment.author?.userId || comment.userId}</span>
                <span class="text-gray-500 text-sm ml-auto">${comment.timestamp}</span>
              </div>
              <p class="text-gray-800 leading-relaxed">${comment.content}</p>
              <div class="flex justify-end mt-2">
                <button class="action-button comment-like-btn ${comment.isLiked ? 'liked' : ''}" 
                        onclick="handleCommentLike('${comment.id}')"
                        style="flex: none; padding: 4px 8px;">
                  <i class="${comment.isLiked ? 'fas' : 'far'} fa-heart"></i>
                  ${comment.likes > 0 ? `<span class="ml-1 text-sm">${comment.likes}</span>` : ''}
                </button>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  
  postsContainer.innerHTML = htmlContent;
}

// 切换下拉菜单
function toggleDropdown() {
  const dropdown = document.getElementById('dropdownMenu');
  dropdown.classList.toggle('hidden');
  
  // 点击其他地方关闭下拉菜单
  setTimeout(() => {
    document.addEventListener('click', function closeDropdown(e) {
      if (!e.target.closest('#sortDropdown') && !e.target.closest('#dropdownMenu')) {
        dropdown.classList.add('hidden');
        document.removeEventListener('click', closeDropdown);
      }
    });
  }, 0);
}

// 选择排序方式
async function selectSort(sortType) {
  currentSortOrder = sortType;
  document.getElementById('dropdownMenu').classList.add('hidden');
  
  // 重新加载评论
  await loadCommentsForCurrentPost();
}

// 处理评论点击
function handleComment(postId) {
  showCommentInput(postId);
}

// 处理帖子点赞
async function handleLike(postId) {
  try {
    const result = await likePost(postId);
    console.log('点赞成功:', result);
    // WebSocket会推送更新，不需要手动更新UI
  } catch (error) {
    console.error('点赞失败:', error);
    showErrorMessage('点赞失败，请重试');
  }
}

// 处理评论点赞
async function handleCommentLike(commentId) {
  try {
    const result = await likeComment(commentId);
    console.log('评论点赞成功:', result);
    // WebSocket会推送更新，不需要手动更新UI
  } catch (error) {
    console.error('评论点赞失败:', error);
    showErrorMessage('评论点赞失败，请重试');
  }
}

// ===== 新增页面渲染函数 =====

// 主渲染函数
function renderCurrentState() {
  console.log('[DEBUG] renderCurrentState 开始执行，当前状态:', currentAppState, '当前视图:', currentView);
  
  switch (currentAppState) {
    case APP_STATES.USER_SELECTION:
      console.log('[DEBUG] 渲染用户选择页面');
      renderUserSelectionPage();
      break;
    case APP_STATES.TEMPLATE_SELECTION:
      console.log('[DEBUG] 渲染模板选择页面');
      renderTemplateSelectionPage();
      break;
    case APP_STATES.MAIN_APP:
      console.log('[DEBUG] 渲染主应用页面');
      if (currentView === 'timeline') {
        console.log('[DEBUG] 渲染时间线，帖子数量:', userPosts?.length);
        renderPosts(userPosts);
      } else if (currentView === 'detail' && currentPost) {
        console.log('[DEBUG] 渲染帖子详情');
        renderPostDetail(currentPost);
      }
      break;
  }
  
  console.log('[DEBUG] renderCurrentState 执行完成');
}

// 渲染用户选择页面
function renderUserSelectionPage() {
  const postsContainer = document.getElementById('postsContainer');
  
  // 如果数据还没加载完成，显示加载状态
  if (!availableUsers || availableUsers.length === 0) {
    postsContainer.innerHTML = `
      <div class="user-selection-page">
        <div class="flex items-center justify-center py-8">
          <div class="text-gray-500">正在加载用户列表...</div>
        </div>
      </div>
    `;
    return;
  }
  
  const content = `
    <div class="user-selection-page">
      <div class="existing-users-section">
        <h2 class="section-title">选择用户</h2>
        <div class="user-grid">
          ${availableUsers.map(user => `
            <button class="user-button" onclick="selectExistingUser(${user.humanUserId})">
              ${user.humanUsername}
            </button>
          `).join('')}
        </div>
      </div>
      
      <div class="create-user-section">
        <h2 class="section-title">创建新用户</h2>
        <div class="create-user-form">
          <input 
            type="text" 
            id="usernameInput" 
            class="user-input" 
            placeholder="输入用户名"
            maxlength="50"
          >
          <button id="createUserBtn" class="create-button" disabled onclick="validateUsername()">
            创建
          </button>
        </div>
      </div>
    </div>
  `;
  
  postsContainer.innerHTML = content;
  setupUsernameValidation();
}

// 渲染模板选择页面
function renderTemplateSelectionPage() {
  const postsContainer = document.getElementById('postsContainer');
  
  const content = `
    <div class="template-selection-page">
      <div class="template-grid">
        ${availableTemplates.map(template => `
          <div class="template-card" onclick="selectTemplate(${template.id})">
            <h3 class="template-name">${template.name}</h3>
            <div class="template-description">
              ${template.persona.substring(0, 200)}...
            </div>
            <button class="template-select-button" onclick="event.stopPropagation(); selectTemplate(${template.id})">
              选择此模板
            </button>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  
  postsContainer.innerHTML = content;
}

// 设置用户名验证
function setupUsernameValidation() {
  const usernameInput = document.getElementById('usernameInput');
  const createBtn = document.getElementById('createUserBtn');
  
  if (usernameInput && createBtn) {
    usernameInput.addEventListener('input', () => {
      const username = usernameInput.value.trim();
      createBtn.disabled = username.length === 0 || username.length > 50;
    });
    
    usernameInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !createBtn.disabled) {
        validateUsername();
      }
    });
  }
}

// 选择现有用户
async function selectExistingUser(userId) {
  try {
    selectedUser = availableUsers.find(u => u.humanUserId === userId);
    
    if (!selectedUser) {
      throw new Error('用户不存在');
    }
    
    // 直接设置为当前用户并进入主应用
    await setCurrentUser(selectedUser.humanUserId);
    currentUser = selectedUser;
    
    // 进入主应用
    currentAppState = APP_STATES.MAIN_APP;
    currentView = 'timeline';
    togglePublishArea(true);
    
    // 加载帖子和初始化WebSocket
    await loadPosts();
    initWebSocket();
    
    renderCurrentState();
    showSuccessMessage(`欢迎回来，${selectedUser.humanUsername}！`);
    
  } catch (error) {
    console.error('选择用户失败:', error);
    showErrorMessage('选择用户失败，请重试');
  }
}

// 验证用户名并进入模板选择
async function validateUsername() {
  const usernameInput = document.getElementById('usernameInput');
  const username = usernameInput.value.trim();
  
  if (username.length === 0 || username.length > 50) {
    showErrorMessage('用户名长度必须在1-50字符之间');
    return;
  }
  
  // 检查用户名是否已存在
  const existingUser = availableUsers.find(u => u.humanUsername === username);
  if (existingUser) {
    showErrorMessage('用户名已存在，请选择其他名称');
    return;
  }
  
  // 保存用户名，进入模板选择
  selectedUser = { username: username };
  currentAppState = APP_STATES.TEMPLATE_SELECTION;
  renderCurrentState();
}

// 选择模板并完成设置
async function selectTemplate(templateId) {
  try {
    let finalUser;
    
    if (selectedUser.humanUserId) {
      // 现有用户，直接设置
      finalUser = selectedUser;
    } else {
      // 新用户，先创建
      finalUser = await createNewUser(selectedUser.username, templateId);
      console.log('用户创建成功:', finalUser);
    }
    
    // 设置为当前用户
    await setCurrentUser(finalUser.humanUserId);
    currentUser = finalUser;
    
    // 进入主应用
    currentAppState = APP_STATES.MAIN_APP;
    currentView = 'timeline';
    togglePublishArea(true);
    
    // 加载帖子和初始化WebSocket
    await loadPosts();
    initWebSocket();
    
    renderCurrentState();
    showSuccessMessage('用户设置完成！');
    
  } catch (error) {
    console.error('设置用户失败:', error);
    showErrorMessage('设置用户失败，请重试');
  }
}