package com.influai.androidapp.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.influai.androidapp.data.local.entity.PostEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PostDao {
    @Query("SELECT * FROM posts ORDER BY createdAtMillis DESC")
    fun getAll(): Flow<List<PostEntity>>

    @Query("SELECT * FROM posts WHERE id = :postId")
    suspend fun getById(postId: Int): PostEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(post: PostEntity): Long

    @Update
    suspend fun update(post: PostEntity)

    @Query("UPDATE posts SET likes = :likes, isLiked = :isLiked WHERE id = :postId")
    suspend fun updateLikes(postId: Int, likes: Int, isLiked: Boolean)

    @Query("UPDATE posts SET commentsCount = :count WHERE id = :postId")
    suspend fun updateCommentsCount(postId: Int, count: Int)
}
