package com.influai.androidapp.data.local.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "comments",
    foreignKeys = [
        ForeignKey(
            entity = PostEntity::class,
            parentColumns = ["id"],
            childColumns = ["postId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("postId")]
)
data class CommentEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val postId: Int,
    val content: String,
    val authorName: String,
    val authorHandle: String,
    val createdAtMillis: Long,
    val likes: Int = 0,
    val isLiked: Boolean = false,
    val senderType: String = "human"
)
