package com.influai.androidapp.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.influai.androidapp.data.local.entity.CommentEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CommentDao {
    @Query("SELECT * FROM comments WHERE postId = :postId ORDER BY createdAtMillis DESC")
    fun getByPostIdOrderByTime(postId: Int): Flow<List<CommentEntity>>

    @Query(
        "SELECT * FROM comments WHERE postId = :postId " +
            "ORDER BY likes DESC, createdAtMillis DESC"
    )
    fun getByPostIdOrderByLikes(postId: Int): Flow<List<CommentEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(comment: CommentEntity): Long

    @Update
    suspend fun update(comment: CommentEntity)

    @Query("SELECT COUNT(*) FROM comments WHERE postId = :postId")
    suspend fun countByPostId(postId: Int): Int

    @Query("UPDATE comments SET likes = :likes, isLiked = :isLiked WHERE id = :commentId")
    suspend fun updateLikes(commentId: Int, likes: Int, isLiked: Boolean)
}
