package com.chessinone.ai

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.chessinone.ai.services.ChessApiService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class FinalReflectionActivity : AppCompatActivity() {

    private lateinit var apiService: ChessApiService
    private var gameId: Int = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_final_reflection)

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

        val btnBackToList = findViewById<Button>(R.id.btnBackToList)
        val tvThinkingPatterns = findViewById<TextView>(R.id.tvThinkingPatterns)
        val tvMissingElements = findViewById<TextView>(R.id.tvMissingElements)
        val tvHabits = findViewById<TextView>(R.id.tvHabits)

        btnBackToList.setOnClickListener {
            finish()
        }

        loadReflection(tvThinkingPatterns, tvMissingElements, tvHabits)
    }

    private fun loadReflection(tvT: TextView, tvM: TextView, tvH: TextView) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val reflection = apiService.getReflection(gameId)
                withContext(Dispatchers.Main) {
                    tvT.text = reflection.thinking_patterns.joinToString("\n\n")
                    tvM.text = reflection.missing_elements.joinToString("\n\n")
                    tvH.text = reflection.habits.joinToString("\n") { "• $it" }
                }
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
}
