package com.influai.androidapp.data.local.model

import androidx.room.Embedded
import androidx.room.Relation
import com.influai.androidapp.data.local.entity.HumanUserEntity
import com.influai.androidapp.data.local.entity.UserTemplateEntity

data class HumanUserWithTemplate(
    @Embedded val user: HumanUserEntity,
    @Relation(
        parentColumn = "templateId",
        entityColumn = "id"
    )
    val template: UserTemplateEntity
)
