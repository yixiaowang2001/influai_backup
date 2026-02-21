package com.influai.androidapp.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "app_state")
data class AppStateEntity(
    @PrimaryKey val id: Int = 1,
    val currentUserId: Int? = null,
    val currentPostId: Int? = null,
    val commentSort: String = "time"
)
