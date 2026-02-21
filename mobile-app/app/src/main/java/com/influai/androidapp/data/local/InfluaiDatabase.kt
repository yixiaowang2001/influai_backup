package com.influai.androidapp.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.influai.androidapp.data.local.dao.AppStateDao
import com.influai.androidapp.data.local.dao.CommentDao
import com.influai.androidapp.data.local.dao.HumanUserDao
import com.influai.androidapp.data.local.dao.PostDao
import com.influai.androidapp.data.local.dao.UserTemplateDao
import com.influai.androidapp.data.local.entity.AppStateEntity
import com.influai.androidapp.data.local.entity.CommentEntity
import com.influai.androidapp.data.local.entity.HumanUserEntity
import com.influai.androidapp.data.local.entity.PostEntity
import com.influai.androidapp.data.local.entity.UserTemplateEntity

@Database(
    entities = [
        UserTemplateEntity::class,
        HumanUserEntity::class,
        PostEntity::class,
        CommentEntity::class,
        AppStateEntity::class
    ],
    version = 4
)
abstract class InfluaiDatabase : RoomDatabase() {
    abstract fun userTemplateDao(): UserTemplateDao
    abstract fun humanUserDao(): HumanUserDao
    abstract fun postDao(): PostDao
    abstract fun commentDao(): CommentDao
    abstract fun appStateDao(): AppStateDao

    companion object {
        const val DB_NAME = "influai.db"
    }
}
