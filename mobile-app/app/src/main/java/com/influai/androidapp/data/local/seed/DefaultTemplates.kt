package com.influai.androidapp.data.local.seed

import com.influai.androidapp.data.local.entity.UserTemplateEntity

object DefaultTemplates {
    val templates: List<UserTemplateEntity> = listOf(
        UserTemplateEntity(
            id = 1,
            name = "STAR",
            persona = "明星用户，拥有大量粉丝，影响力强",
            followerCount = 1000000
        ),
        UserTemplateEntity(
            id = 2,
            name = "CASTER",
            persona = "媒体人用户，关注热点事件，表达清晰",
            followerCount = 120000
        ),
        UserTemplateEntity(
            id = 3,
            name = "NORMAL",
            persona = "普通用户，日常分享生活与观点",
            followerCount = 8000
        )
    )
}
