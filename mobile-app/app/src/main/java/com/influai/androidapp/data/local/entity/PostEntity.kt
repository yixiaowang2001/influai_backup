package com.influai.androidapp.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "posts")
data class PostEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val content: String,
    val authorName: String,
    val authorHandle: String,
    val createdAtMillis: Long,
    val likes: Int = 0,
    val isLiked: Boolean = false,
    val commentsCount: Int = 0
)
