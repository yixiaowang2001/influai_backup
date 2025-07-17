// 用户帖子存储
let userPosts = [];

// 默认用户信息
const defaultUser = {
  username: '默认用户',
  userId: '@example_user'
};

// 当前页面状态
let currentView = 'timeline'; // 'timeline' 或 'detail'
let currentPost = null;
let isCommentInputVisible = false; // 评论输入框是否显示
let currentSortOrder = 'time'; // 'time' 或 'likes'

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', () => {
  const commentInput = document.getElementById('postContent');
  const postButton = document.getElementById('postButton');
  const charCount = document.getElementById('charCount');
  const postsContainer = document.getElementById('postsContainer');
  
  // 初始化帖子列表（显示空状态）
  renderPosts(userPosts);
  
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
      // 创建新帖子
      const newPost = {
        id: Date.now(), // 使用时间戳作为ID
        username: defaultUser.username,
        userId: defaultUser.userId,
        content: content,
        timestamp: formatTimestamp(new Date()),
        likes: 0,
        comments: [], // 空的评论数组，不再添加示例评论
        createdAt: new Date(),
        isLiked: false // 是否已点赞
      };
      
      // 添加到帖子列表顶部（新的在上）
      userPosts.unshift(newPost);
      
      // 清空输入框
      commentInput.value = '';
      charCount.textContent = '0';
      
      // 重新渲染帖子列表
      renderPosts(userPosts);
    } catch (error) {
      console.error('发布失败:', error);
    } finally {
      // 恢复按钮状态
      postButton.disabled = content.length === 0 || content.length > 140;
      postButton.textContent = '发布';
    }
  });
});

// 控制发布框显示/隐藏
function togglePublishArea(show) {
  const publishArea = document.getElementById('publishArea');
  if (show) {
    publishArea.classList.remove('hidden');
  } else {
    publishArea.classList.add('hidden');
  }
}

// 排序评论
function sortComments(comments, order) {
  if (order === 'likes') {
    return [...comments].sort((a, b) => b.likes - a.likes);
  } else {
    return [...comments].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  }
}

// 切换排序方式
function toggleSortOrder(newOrder) {
  currentSortOrder = newOrder;
  if (currentPost) {
    renderPostDetail(currentPost);
  }
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
function submitComment(postId) {
  const commentContent = document.getElementById('commentContent').value.trim();
  if (!commentContent || commentContent.length > 140) return;
  
  const post = userPosts.find(p => p.id === postId);
  if (!post) return;
  
  // 创建新评论
  const newComment = {
    id: `${postId}_${Date.now()}`,
    username: defaultUser.username,
    userId: defaultUser.userId,
    content: commentContent,
    timestamp: formatTimestamp(new Date()),
    likes: 0,
    isLiked: false,
    createdAt: new Date()
  };
  
  // 添加评论到帖子
  post.comments.push(newComment);
  
  // 隐藏输入框
  hideCommentInput();
  
  // 重新渲染页面
  if (currentView === 'detail' && currentPost && currentPost.id === postId) {
    renderPostDetail(post);
  } else {
    renderPosts(userPosts);
  }
}

// 点击帖子进入详情页
function viewPostDetail(postId) {
  const post = userPosts.find(p => p.id === postId);
  if (post) {
    currentView = 'detail';
    currentPost = post;
    togglePublishArea(false); // 隐藏发布框
    renderPostDetail(post);
  }
}

// 返回时间线
function backToTimeline() {
  currentView = 'timeline';
  currentPost = null;
  hideCommentInput(); // 确保隐藏评论输入框
  togglePublishArea(true); // 显示发布框
  renderPosts(userPosts);
}

// 渲染帖子列表
function renderPosts(posts) {
  const postsContainer = document.getElementById('postsContainer');
  
  if (posts.length === 0) {
    postsContainer.innerHTML = '';
    return;
  }
  
  // 生成帖子HTML - 使用扁平样式，细灰线分隔
  const htmlContent = posts.map(post => `
    <div class="post-item">
      <div class="p-4 cursor-pointer" onclick="viewPostDetail(${post.id})">
        <div class="flex items-center mb-3">
          <div class="font-medium text-gray-900">${post.username}</div>
          <span class="text-gray-500 text-sm ml-2">${post.userId}</span>
          <span class="text-gray-500 text-sm ml-auto">${post.timestamp}</span>
        </div>
        <p class="text-gray-800 leading-relaxed">${post.content}</p>
      </div>
      <div class="actions-bar">
        <button class="action-button comment-btn" onclick="event.stopPropagation(); showCommentInput(${post.id})">
          <i class="far fa-comment"></i>
        </button>
        <button class="action-button like-btn ${post.isLiked ? 'liked' : ''}" onclick="event.stopPropagation(); handleLike(${post.id})">
          <i class="${post.isLiked ? 'fas' : 'far'} fa-heart"></i>
          ${post.likes > 0 ? `<span class="ml-1 text-sm">${post.likes}</span>` : ''}
        </button>
      </div>
    </div>
  `).join('');
  
  postsContainer.innerHTML = htmlContent;
}

// 渲染帖子详情页面
function renderPostDetail(post) {
  const postsContainer = document.getElementById('postsContainer');
  
  // 排序评论
  const sortedComments = sortComments(post.comments, currentSortOrder);
  
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
        <div class="p-4 cursor-pointer" onclick="showCommentInput(${post.id})">
          <div class="flex items-center mb-3">
            <div class="font-medium text-gray-900">${post.username}</div>
            <span class="text-gray-500 text-sm ml-2">${post.userId}</span>
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
          <span class="text-gray-600">共 ${post.comments.length} 条评论</span>
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
                <div class="font-medium text-gray-900">${comment.username}</div>
                <span class="text-gray-500 text-sm ml-2">${comment.userId}</span>
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
function selectSort(sortType) {
  currentSortOrder = sortType;
  document.getElementById('dropdownMenu').classList.add('hidden');
  renderPostDetail(currentPost);
}

// 处理评论点击
function handleComment(postId) {
  showCommentInput(postId);
}

// 处理帖子点赞
function handleLike(postId) {
  // 找到对应的帖子
  const post = userPosts.find(p => p.id === postId);
  if (post && !post.isLiked) {
    post.likes += 1;
    post.isLiked = true;
    
    // 根据当前页面状态重新渲染
    if (currentView === 'timeline') {
      renderPosts(userPosts);
    } else if (currentView === 'detail' && currentPost && currentPost.id === postId) {
      renderPostDetail(post);
    }
  }
}

// 处理评论点赞
function handleCommentLike(commentId) {
  if (currentPost) {
    const comment = currentPost.comments.find(c => c.id === commentId);
    if (comment && !comment.isLiked) {
      comment.likes += 1;
      comment.isLiked = true;
      renderPostDetail(currentPost);
    }
  }
}