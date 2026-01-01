package com.chessinone.ai

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.chessinone.ai.services.ChessApiService
import com.chessinone.ai.services.GameMetadata
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class CreateGameActivity : AppCompatActivity() {

    private lateinit var apiService: ChessApiService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_create_game)

        val retrofit = Retrofit.Builder()
            .baseUrl("https://chess-coach.tailnet-xyz.ts.net/") // Tailscale Funnel Address
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        apiService = retrofit.create(ChessApiService::class.java)

        val btnCreate = findViewById<Button>(R.id.btnCreate)
        val etOpponent = findViewById<EditText>(R.id.etOpponent)
        val etEvent = findViewById<EditText>(R.id.etEvent)
        val etTimeControl = findViewById<EditText>(R.id.etTimeControl)
        val spinnerColor = findViewById<Spinner>(R.id.spinnerColor)

        btnCreate.setOnClickListener {
            val metadata = GameMetadata(
                player_color = spinnerColor.selectedItem?.toString()?.uppercase() ?: "WHITE",
                opponent_name = etOpponent.text.toString(),
                event = etEvent.text.toString(),
                date = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).format(java.util.Date()),
                time_control = etTimeControl.text.toString()
            )

            if (metadata.opponent_name.isEmpty()) {
                Toast.makeText(this, "Opponent name required", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            CoroutineScope(Dispatchers.IO).launch {
                try {
                    val game = apiService.createGame(metadata)
                    withContext(Dispatchers.Main) {
                        val intent = Intent(this@CreateGameActivity, GameEntryActivity::class.java)
                        intent.putExtra("GAME_ID", game.id)
                        startActivity(intent)
                        finish()
                    }
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        Toast.makeText(this@CreateGameActivity, "Failed to create game", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        }
    }
}
