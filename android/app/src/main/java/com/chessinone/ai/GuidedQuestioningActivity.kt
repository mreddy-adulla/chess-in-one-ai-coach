package com.chessinone.ai

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.chessinone.ai.services.AnswerRequest
import com.chessinone.ai.services.ChessApiService
import com.chessinone.ai.services.QuestionResponse
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class GuidedQuestioningActivity : AppCompatActivity() {

    private lateinit var apiService: ChessApiService
    private var gameId: Int = -1
    private var currentQuestionId: Int = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_guided_questioning)

        gameId = intent.getIntExtra("GAME_ID", -1)
        if (gameId == -1) {
            finish()
            return
        }

        val retrofit = Retrofit.Builder()
            .baseUrl("https://chess-coach.tailnet-xyz.ts.net/") // Tailscale Funnel Address
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        apiService = retrofit.create(ChessApiService::class.java)

        val btnSubmitAnswer = findViewById<Button>(R.id.btnSubmitAnswer)
        val btnSkipQuestion = findViewById<Button>(R.id.btnSkipQuestion)
        val etAnswer = findViewById<EditText>(R.id.etAnswer)
        val tvQuestion = findViewById<TextView>(R.id.tvQuestion)

        btnSubmitAnswer.setOnClickListener {
            submitAnswer(etAnswer.text.toString(), false)
        }

        btnSkipQuestion.setOnClickListener {
            submitAnswer("", true)
        }

        loadNextQuestion(tvQuestion)
    }

    private fun loadNextQuestion(tv: TextView) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val question = apiService.getNextQuestion(gameId)
                withContext(Dispatchers.Main) {
                    currentQuestionId = question.id
                    tv.text = question.question_text
                    findViewById<EditText>(R.id.etAnswer).setText("")
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    // Assume session complete
                    val intent = Intent(this@GuidedQuestioningActivity, FinalReflectionActivity::class.java)
                    intent.putExtra("GAME_ID", gameId)
                    startActivity(intent)
                    finish()
                }
            }
        }
    }

    private fun submitAnswer(content: String, skipped: Boolean) {
        if (currentQuestionId == -1) return

        CoroutineScope(Dispatchers.IO).launch {
            try {
                apiService.answerQuestion(currentQuestionId, AnswerRequest(content, skipped))
                withContext(Dispatchers.Main) {
                    loadNextQuestion(findViewById(R.id.tvQuestion))
                }
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
}
