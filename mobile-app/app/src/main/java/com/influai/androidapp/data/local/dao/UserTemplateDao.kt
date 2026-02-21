package com.influai.androidapp.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.influai.androidapp.data.local.entity.UserTemplateEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface UserTemplateDao {
    @Query("SELECT * FROM user_templates")
    fun getAll(): Flow<List<UserTemplateEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(templates: List<UserTemplateEntity>)

    @Query("SELECT COUNT(*) FROM user_templates")
    suspend fun count(): Int
}
