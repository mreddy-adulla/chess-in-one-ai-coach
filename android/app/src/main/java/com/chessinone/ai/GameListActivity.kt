package com.chessinone.ai

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.chessinone.ai.services.ChessApiService
import com.chessinone.ai.services.GameSummary
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class GameListActivity : AppCompatActivity() {

    private lateinit var apiService: ChessApiService
    private lateinit var btnCreateGame: Button
    private lateinit var rvGames: RecyclerView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_game_list)

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/") // Android Emulator loopback to host
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        apiService = retrofit.create(ChessApiService::class.java)

        btnCreateGame = findViewById(R.id.btnCreateGame)
        rvGames = findViewById(R.id.rvGames)
        rvGames.layoutManager = LinearLayoutManager(this)

        btnCreateGame.setOnClickListener {
            startActivity(Intent(this, CreateGameActivity::class.java))
        }

        loadGames()
    }

    private fun loadGames() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val games = apiService.getGames()
                withContext(Dispatchers.Main) {
                    // Set up adapter for rvGames
                }
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
}
