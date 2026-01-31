package com.influai.androidapp.ui.model

data class UserTemplate(
    val id: Int,
    val name: String,
    val persona: String,
    val followerCount: Int
)

data class HumanUser(
    val id: Int,
    val username: String,
    val template: UserTemplate,
    val followerCount: Int,
    val avatarPath: String = ""
)
