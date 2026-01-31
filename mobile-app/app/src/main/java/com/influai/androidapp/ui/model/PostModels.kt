package com.influai.androidapp.ui.model

data class PostItem(
    val id: Int,
    val content: String,
    val authorName: String,
    val authorHandle: String,
    val createdAtMillis: Long,
    val likes: Int = 0,
    val isLiked: Boolean = false,
    val commentsCount: Int = 0
)

data class CommentItem(
    val id: Int,
    val postId: Int,
    val content: String,
    val authorName: String,
    val authorHandle: String,
    val createdAtMillis: Long,
    val likes: Int = 0,
    val isLiked: Boolean = false,
    val senderType: String = "human"
)
