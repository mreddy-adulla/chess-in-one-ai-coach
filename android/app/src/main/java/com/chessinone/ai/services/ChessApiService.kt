package com.chessinone.ai.services

import retrofit2.http.POST
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Body

interface ChessApiService {
    @GET("games")
    suspend fun getGames(): List<GameSummary>

    @POST("games")
    suspend fun createGame(@Body metadata: GameMetadata): GameSummary

    @GET("games/{id}")
    suspend fun getGame(@Path("id") gameId: Int): GameDetail

    @POST("games/{id}/annotations")
    suspend fun addAnnotation(@Path("id") gameId: Int, @Body annotation: AnnotationRequest): ApiResponse

    @POST("games/{id}/submit")
    suspend fun submitGame(@Path("id") gameId: Int): ApiResponse

    @GET("games/{id}/next-question")
    suspend fun getNextQuestion(@Path("id") gameId: Int): QuestionResponse

    @POST("questions/{id}/answer")
    suspend fun answerQuestion(@Path("id") questionId: Int, @Body request: AnswerRequest): ApiResponse

    @GET("games/{id}/reflection")
    suspend fun getReflection(@Path("id") gameId: Int): ReflectionResponse
}

data class GameMetadata(
    val player_color: String,
    val opponent_name: String,
    val event: String,
    val date: String,
    val time_control: String
)

data class GameSummary(
    val id: Int,
    val opponent_name: String,
    val state: String,
    val created_at: String
)

data class GameDetail(
    val id: Int,
    val opponent_name: String,
    val state: String,
    val created_at: String
    // Add other fields as needed
)

data class AnnotationRequest(
    val move_number: Int,
    val content: String
)

data class ApiResponse(val message: String, val state: String?)

data class QuestionResponse(val id: Int, val question_text: String, val category: String)

data class AnswerRequest(val content: String, val skipped: Boolean)

data class ReflectionResponse(
    val thinking_patterns: List<String>,
    val missing_elements: List<String>,
    val habits: List<String>
)
