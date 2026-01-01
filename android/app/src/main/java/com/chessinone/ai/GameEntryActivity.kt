package com.chessinone.ai

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.chessinone.ai.services.AnnotationRequest
import com.chessinone.ai.services.ChessApiService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class GameEntryActivity : AppCompatActivity() {

    private lateinit var apiService: ChessApiService
    private var gameId: Int = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_game_entry)

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

        val btnSaveAnnotation = findViewById<Button>(R.id.btnSaveAnnotation)
        val btnSubmitToAI = findViewById<Button>(R.id.btnSubmitToAI)
        val etAnnotation = findViewById<EditText>(R.id.etAnnotation)
        val tvGameMeta = findViewById<TextView>(R.id.tvGameMeta)

        loadGameDetails(tvGameMeta)

        btnSaveAnnotation.setOnClickListener {
            val content = etAnnotation.text.toString()
            if (content.isEmpty()) return@setOnClickListener

            CoroutineScope(Dispatchers.IO).launch {
                try {
                    apiService.addAnnotation(gameId, 1, AnnotationRequest(1, content)) // Placeholder move number
                    withContext(Dispatchers.Main) {
                        etAnnotation.setText("")
                        Toast.makeText(this@GameEntryActivity, "Saved", Toast.LENGTH_SHORT).show()
                    }
                } catch (e: Exception) {
                    // Handle error
                }
            }
        }

        btnSubmitToAI.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("Submit to AI")
                .setMessage("Irreversible: Lock annotations and start coaching?")
                .setPositiveButton("Confirm") { _, _ ->
                    submitToAI()
                }
                .setNegativeButton("Cancel", null)
                .show()
        }
    }

    private fun loadGameDetails(tv: TextView) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val game = apiService.getGame(gameId)
                withContext(Dispatchers.Main) {
                    tv.text = "vs ${game.opponent_name} (${game.state})"
                }
            } catch (e: Exception) {}
        }
    }

    private fun submitToAI() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                apiService.submitGame(gameId)
                withContext(Dispatchers.Main) {
                    val intent = Intent(this@GameEntryActivity, GuidedQuestioningActivity::class.java)
                    intent.putExtra("GAME_ID", gameId)
                    startActivity(intent)
                    finish()
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@GameEntryActivity, "Submission failed", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}
