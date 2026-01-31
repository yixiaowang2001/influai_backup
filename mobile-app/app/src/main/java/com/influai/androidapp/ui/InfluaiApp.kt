package com.influai.androidapp.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.influai.androidapp.ui.model.HumanUser
import com.influai.androidapp.ui.model.CommentItem
import com.influai.androidapp.ui.model.PostItem
import com.influai.androidapp.ui.model.UserTemplate
import kotlinx.coroutines.launch
import kotlin.math.max

private enum class AppScreen {
    UserSelection,
    UsernameInput,
    TemplateSelection,
    Timeline,
    PostDetail
}

private enum class CommentSort {
    Time,
    Likes
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InfluaiApp(modifier: Modifier = Modifier) {
    var currentScreen by rememberSaveable { mutableStateOf(AppScreen.UserSelection) }
    val snackbarHostState = remember { SnackbarHostState() }
    val coroutineScope = androidx.compose.runtime.rememberCoroutineScope()

    val templates = remember {
        listOf(
            UserTemplate(
                id = 1,
                name = "STAR",
                persona = "明星用户，拥有大量粉丝，影响力强",
                followerCount = 1000000
            ),
            UserTemplate(
                id = 2,
                name = "CASTER",
                persona = "媒体人用户，关注热点事件，表达清晰",
                followerCount = 120000
            ),
            UserTemplate(
                id = 3,
                name = "NORMAL",
                persona = "普通用户，日常分享生活与观点",
                followerCount = 8000
            )
        )
    }

    val users = remember { mutableStateListOf<HumanUser>() }
    var currentUser by remember { mutableStateOf<HumanUser?>(null) }
    var pendingUsername by remember { mutableStateOf<String?>(null) }
    var nextUserId by remember { mutableStateOf(1) }
    val posts = remember { mutableStateListOf<PostItem>() }
    var nextPostId by remember { mutableStateOf(1) }
    var currentPost by remember { mutableStateOf<PostItem?>(null) }
    val commentsByPostId = remember { mutableStateMapOf<Int, SnapshotStateList<CommentItem>>() }
    var nextCommentId by remember { mutableStateOf(1) }
    var commentSort by rememberSaveable { mutableStateOf(CommentSort.Time) }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = { Text(screenTitle(currentScreen)) }
            )
        },
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) }
    ) { innerPadding ->
        when (currentScreen) {
            AppScreen.UserSelection -> UserSelectionScreen(
                users = users,
                onCreateNew = {
                    pendingUsername = null
                    currentScreen = AppScreen.UsernameInput
                },
                onEnter = { user ->
                    currentUser = user
                    currentScreen = AppScreen.Timeline
                    showMessage(coroutineScope, snackbarHostState, "欢迎回来，${user.username}！")
                },
                onDeleteUser = { user ->
                    val wasCurrent = currentUser?.id == user.id
                    users.remove(user)
                    if (wasCurrent) {
                        currentUser = null
                        currentScreen = AppScreen.UserSelection
                    }
                    showMessage(coroutineScope, snackbarHostState, "已删除账号：${user.username}")
                },
                modifier = Modifier.padding(innerPadding)
            )
            AppScreen.UsernameInput -> UsernameInputScreen(
                onNext = { username ->
                    if (users.any { it.username == username }) {
                        showMessage(coroutineScope, snackbarHostState, "用户名已存在，请更换")
                    } else {
                        pendingUsername = username
                        currentScreen = AppScreen.TemplateSelection
                    }
                },
                onBack = { currentScreen = AppScreen.UserSelection },
                modifier = Modifier.padding(innerPadding)
            )
            AppScreen.TemplateSelection -> TemplateSelectionScreen(
                templates = templates,
                onSelectTemplate = { template ->
                    val username = pendingUsername
                    if (username.isNullOrBlank()) {
                        showMessage(coroutineScope, snackbarHostState, "用户名信息丢失，请重新创建")
                        currentScreen = AppScreen.UsernameInput
                        return@TemplateSelectionScreen
                    }
                    val newUser = HumanUser(
                        id = nextUserId,
                        username = username,
                        template = template,
                        followerCount = template.followerCount
                    )
                    nextUserId += 1
                    users.add(newUser)
                    currentUser = newUser
                    pendingUsername = null
                    currentScreen = AppScreen.Timeline
                    showMessage(coroutineScope, snackbarHostState, "账号创建成功：${newUser.username}")
                },
                onBack = { currentScreen = AppScreen.UsernameInput },
                modifier = Modifier.padding(innerPadding)
            )
            AppScreen.Timeline -> TimelineScreen(
                posts = posts,
                onCreatePost = { content ->
                    val author = currentUser
                    if (author == null) {
                        showMessage(coroutineScope, snackbarHostState, "请先选择账号")
                        return@TimelineScreen
                    }
                    val newPost = PostItem(
                        id = nextPostId,
                        content = content,
                        authorName = author.username,
                        authorHandle = "@${author.username.lowercase()}",
                        createdAtMillis = System.currentTimeMillis()
                    )
                    nextPostId += 1
                    posts.add(0, newPost)
                    showMessage(coroutineScope, snackbarHostState, "帖子发布成功")
                },
                onToggleLike = { post ->
                    val updated = post.copy(
                        isLiked = !post.isLiked,
                        likes = max(0, post.likes + if (post.isLiked) -1 else 1)
                    )
                    val index = posts.indexOfFirst { it.id == post.id }
                    if (index >= 0) {
                        posts[index] = updated
                    }
                },
                onOpenDetail = { post ->
                    currentPost = post
                    ensureCommentsList(commentsByPostId, post.id)
                    currentScreen = AppScreen.PostDetail
                },
                onBackToUsers = {
                    currentUser = null
                    currentScreen = AppScreen.UserSelection
                    showMessage(coroutineScope, snackbarHostState, "已退出当前账号")
                },
                currentUser = currentUser,
                modifier = Modifier.padding(innerPadding)
            )
            AppScreen.PostDetail -> PostDetailScreen(
                post = currentPost,
                comments = currentPost?.let { commentsByPostId[it.id] } ?: emptyList(),
                sort = commentSort,
                onChangeSort = { commentSort = it },
                onToggleCommentLike = { comment ->
                    val list = commentsByPostId[comment.postId] ?: return@PostDetailScreen
                    val updated = comment.copy(
                        isLiked = !comment.isLiked,
                        likes = max(0, comment.likes + if (comment.isLiked) -1 else 1)
                    )
                    val index = list.indexOfFirst { it.id == comment.id }
                    if (index >= 0) {
                        list[index] = updated
                    }
                },
                onAddComment = { content ->
                    val post = currentPost
                    val author = currentUser
                    if (post == null) {
                        showMessage(coroutineScope, snackbarHostState, "未找到帖子")
                        return@PostDetailScreen
                    }
                    if (author == null) {
                        showMessage(coroutineScope, snackbarHostState, "请先选择账号")
                        return@PostDetailScreen
                    }
                    val list = ensureCommentsList(commentsByPostId, post.id)
                    val newComment = CommentItem(
                        id = nextCommentId,
                        postId = post.id,
                        content = content,
                        authorName = author.username,
                        authorHandle = "@${author.username.lowercase()}",
                        createdAtMillis = System.currentTimeMillis(),
                        senderType = "human"
                    )
                    nextCommentId += 1
                    list.add(0, newComment)
                    updatePostCommentsCount(posts, post.id, list.size)
                    currentPost = posts.firstOrNull { it.id == post.id }
                    showMessage(coroutineScope, snackbarHostState, "评论发布成功")
                },
                onBack = { currentScreen = AppScreen.Timeline },
                modifier = Modifier.padding(innerPadding)
            )
        }
    }
}

private fun screenTitle(screen: AppScreen): String {
    return when (screen) {
        AppScreen.UserSelection -> "账号选择"
        AppScreen.UsernameInput -> "创建新账号"
        AppScreen.TemplateSelection -> "选择模板"
        AppScreen.Timeline -> "时间线"
        AppScreen.PostDetail -> "帖子详情"
    }
}

@Composable
private fun UserSelectionScreen(
    users: List<HumanUser>,
    onCreateNew: () -> Unit,
    onEnter: (HumanUser) -> Unit,
    onDeleteUser: (HumanUser) -> Unit,
    modifier: Modifier = Modifier
) {
    var pendingDelete by remember { mutableStateOf<HumanUser?>(null) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("选择你的账号")
        if (users.isEmpty()) {
            Text("暂无账号，请先创建")
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentPadding = PaddingValues(vertical = 4.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(users, key = { it.id }) { user ->
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text("用户名：${user.username}")
                            Text("模板：${user.template.name}")
                            Text("粉丝数：${user.followerCount}")
                            Text("人设：${user.template.persona}")
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Button(onClick = { onEnter(user) }, modifier = Modifier.fillMaxWidth()) {
                                    Text("进入")
                                }
                                Button(onClick = { pendingDelete = user }, modifier = Modifier.fillMaxWidth()) {
                                    Text("删除")
                                }
                            }
                        }
                    }
                }
            }
        }
        Button(onClick = onCreateNew, modifier = Modifier.fillMaxWidth()) {
            Text("创建新账号")
        }
    }

    if (pendingDelete != null) {
        AlertDialog(
            onDismissRequest = { pendingDelete = null },
            title = { Text("确认删除账号") },
            text = { Text("此操作将删除账号及其数据，是否继续？") },
            confirmButton = {
                Button(onClick = {
                    pendingDelete?.let { onDeleteUser(it) }
                    pendingDelete = null
                }) {
                    Text("确认删除")
                }
            },
            dismissButton = {
                Button(onClick = { pendingDelete = null }) {
                    Text("取消")
                }
            }
        )
    }
}

@Composable
private fun UsernameInputScreen(
    onNext: (String) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    var username by rememberSaveable { mutableStateOf("") }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        OutlinedTextField(
            value = username,
            onValueChange = { username = it },
            label = { Text("用户名") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(
            onClick = { onNext(username.trim()) },
            enabled = username.isNotBlank(),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("下一步")
        }
        Button(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
            Text("返回")
        }
    }
}

@Composable
private fun TemplateSelectionScreen(
    templates: List<UserTemplate>,
    onSelectTemplate: (UserTemplate) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("选择账号模板")
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentPadding = PaddingValues(vertical = 4.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(templates, key = { it.id }) { template ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("模板：${template.name}")
                        Text("粉丝数：${template.followerCount}")
                        Text("人设：${template.persona}")
                        Button(
                            onClick = { onSelectTemplate(template) },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("选择此模板")
                        }
                    }
                }
            }
        }
        Button(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
            Text("返回")
        }
    }
}

@Composable
private fun TimelineScreen(
    posts: List<PostItem>,
    onCreatePost: (String) -> Unit,
    onToggleLike: (PostItem) -> Unit,
    onOpenDetail: (PostItem) -> Unit,
    onBackToUsers: () -> Unit,
    currentUser: HumanUser?,
    modifier: Modifier = Modifier
) {
    var postContent by rememberSaveable { mutableStateOf("") }
    val trimmed = postContent.trim()
    val canPost = trimmed.isNotEmpty() && trimmed.length <= 140

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        if (currentUser != null) {
            Text("当前账号：${currentUser.username}")
        }
        Button(onClick = onBackToUsers, modifier = Modifier.fillMaxWidth()) {
            Text("返回账号选择")
        }
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentPadding = PaddingValues(vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(posts, key = { it.id }) { post ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(post.authorName)
                            Text(post.authorHandle)
                            Text(formatTimestamp(post.createdAtMillis))
                        }
                        Text(post.content, modifier = Modifier.padding(top = 6.dp))
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 8.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Button(onClick = { onOpenDetail(post) }) {
                                Text("评论 ${post.commentsCount}")
                            }
                            Button(onClick = { onToggleLike(post) }) {
                                Text(if (post.isLiked) "已赞 ${post.likes}" else "赞 ${post.likes}")
                            }
                        }
                    }
                }
            }
        }
        OutlinedTextField(
            value = postContent,
            onValueChange = { postContent = it },
            label = { Text("分享新鲜事...") },
            modifier = Modifier.fillMaxWidth()
        )
        Text("${postContent.length}/140")
        Button(
            onClick = {
                onCreatePost(trimmed)
                postContent = ""
            },
            enabled = canPost,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("发布")
        }
    }
}

@Composable
private fun PostDetailScreen(
    post: PostItem?,
    comments: List<CommentItem>,
    sort: CommentSort,
    onChangeSort: (CommentSort) -> Unit,
    onToggleCommentLike: (CommentItem) -> Unit,
    onAddComment: (String) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    var commentContent by rememberSaveable { mutableStateOf("") }
    val trimmed = commentContent.trim()
    val canSend = trimmed.isNotEmpty() && trimmed.length <= 140
    val sortedComments = when (sort) {
        CommentSort.Time -> comments.sortedByDescending { it.createdAtMillis }
        CommentSort.Likes -> comments.sortedByDescending { it.likes }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Button(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
            Text("返回时间线")
        }
        if (post != null) {
            Text("作者：${post.authorName} ${post.authorHandle}")
            Text("时间：${formatTimestamp(post.createdAtMillis)}")
            Text(post.content, modifier = Modifier.padding(top = 6.dp))
            Text("赞 ${post.likes} · 评论 ${post.commentsCount}")
        } else {
            Text("帖子内容展示区域")
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Button(onClick = { onChangeSort(CommentSort.Time) }) {
                Text(if (sort == CommentSort.Time) "按时间排序 ✓" else "按时间排序")
            }
            Button(onClick = { onChangeSort(CommentSort.Likes) }) {
                Text(if (sort == CommentSort.Likes) "按点赞排序 ✓" else "按点赞排序")
            }
        }
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentPadding = PaddingValues(vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(sortedComments, key = { it.id }) { comment ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(comment.authorName)
                            Text(comment.authorHandle)
                            Text(formatTimestamp(comment.createdAtMillis))
                        }
                        Text(comment.content, modifier = Modifier.padding(top = 6.dp))
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(top = 6.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Spacer(modifier = Modifier.weight(1f))
                            Button(onClick = { onToggleCommentLike(comment) }) {
                                Text(if (comment.isLiked) "已赞 ${comment.likes}" else "赞 ${comment.likes}")
                            }
                        }
                    }
                }
            }
        }
        OutlinedTextField(
            value = commentContent,
            onValueChange = { commentContent = it },
            label = { Text("写评论...") },
            modifier = Modifier.fillMaxWidth()
        )
        Text("${commentContent.length}/140")
        Button(
            onClick = {
                onAddComment(trimmed)
                commentContent = ""
            },
            enabled = canSend,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("评论")
        }
    }
}

private fun showMessage(
    coroutineScope: kotlinx.coroutines.CoroutineScope,
    hostState: SnackbarHostState,
    message: String
) {
    coroutineScope.launch {
        hostState.showSnackbar(message)
    }
}

private fun formatTimestamp(createdAtMillis: Long): String {
    val diffSeconds = (System.currentTimeMillis() - createdAtMillis) / 1000
    return when {
        diffSeconds < 60 -> "刚刚"
        diffSeconds < 3600 -> "${diffSeconds / 60}分钟前"
        diffSeconds < 86400 -> "${diffSeconds / 3600}小时前"
        else -> "${diffSeconds / 86400}天前"
    }
}

private fun ensureCommentsList(
    map: MutableMap<Int, SnapshotStateList<CommentItem>>,
    postId: Int
): SnapshotStateList<CommentItem> {
    return map.getOrPut(postId) { mutableStateListOf() }
}

private fun updatePostCommentsCount(
    posts: MutableList<PostItem>,
    postId: Int,
    count: Int
) {
    val index = posts.indexOfFirst { it.id == postId }
    if (index >= 0) {
        val post = posts[index]
        posts[index] = post.copy(commentsCount = count)
    }
}
