package com.influai.androidapp.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.influai.androidapp.data.local.entity.HumanUserEntity
import com.influai.androidapp.data.local.model.HumanUserWithTemplate
import kotlinx.coroutines.flow.Flow

@Dao
interface HumanUserDao {
    @Transaction
    @Query("SELECT * FROM human_users")
    fun getAllWithTemplate(): Flow<List<HumanUserWithTemplate>>

    @Transaction
    @Query("SELECT * FROM human_users WHERE id = :userId")
    suspend fun getByIdWithTemplate(userId: Int): HumanUserWithTemplate?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(user: HumanUserEntity): Long

    @Delete
    suspend fun delete(user: HumanUserEntity)

    @Query("DELETE FROM human_users WHERE id = :userId")
    suspend fun deleteById(userId: Int)
}
