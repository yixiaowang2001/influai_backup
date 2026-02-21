package com.influai.androidapp.data.local.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "human_users",
    foreignKeys = [
        ForeignKey(
            entity = UserTemplateEntity::class,
            parentColumns = ["id"],
            childColumns = ["templateId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("templateId")]
)
data class HumanUserEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val username: String,
    val templateId: Int,
    val followerCount: Int,
    val avatarPath: String = ""
)
