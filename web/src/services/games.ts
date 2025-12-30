import { ApiService } from "../services/api";

export interface GameMetadata {
  player_color: "WHITE" | "BLACK";
  opponent_name: string;
  event: string;
  date: string;
  time_control: string;
}

export async function getGames() {
  return ApiService.request("/games");
}

export async function createGame(metadata: GameMetadata) {
  return ApiService.request("/games", {
    method: "POST",
    body: JSON.stringify(metadata),
  });
}

export async function getGame(gameId: number) {
  return ApiService.request(`/games/${gameId}`);
}

export async function addAnnotation(gameId: number, moveNumber: number, content: string) {
  return ApiService.request(`/games/${gameId}/annotations`, {
    method: "POST",
    body: JSON.stringify({ move_number: moveNumber, content }),
  });
}

export async function submitGame(gameId: number) {
  return ApiService.request(`/games/${gameId}/submit`, {
    method: "POST",
  });
}

export async function getNextQuestion(gameId: number) {
  return ApiService.request(`/games/${gameId}/next-question`);
}

export async function answerQuestion(questionId: number, answer: string, skipped: boolean = false) {
  return ApiService.request(`/questions/${questionId}/answer`, {
    method: "POST",
    body: JSON.stringify({ content: answer, skipped }),
  });
}

export async function getReflection(gameId: number) {
  return ApiService.request(`/games/${gameId}/reflection`);
}

export async function getPciUsage() {
  return ApiService.request("/pci/usage");
}

export async function getPciSettings() {
  return ApiService.request("/pci/settings");
}

export async function getAvailableModels() {
  return ApiService.request("/pci/available-models");
}

export async function updatePciSettings(settings: Record<string, string>) {
  return ApiService.request("/pci/settings", {
    method: "POST",
    body: JSON.stringify({ settings }),
  });
}

export async function approvePciSession(approvalId: number, decision: 'APPROVE' | 'DENY') {
  return ApiService.request(`/pci/approvals/${approvalId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
}
