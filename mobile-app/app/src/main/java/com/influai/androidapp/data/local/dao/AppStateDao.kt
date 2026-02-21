package com.influai.androidapp.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.influai.androidapp.data.local.entity.AppStateEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface AppStateDao {
    @Query("SELECT * FROM app_state WHERE id = 1")
    fun getState(): Flow<AppStateEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(state: AppStateEntity)
}
