package com.influai.androidapp.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "user_templates")
data class UserTemplateEntity(
    @PrimaryKey val id: Int,
    val name: String,
    val persona: String,
    val followerCount: Int
)
