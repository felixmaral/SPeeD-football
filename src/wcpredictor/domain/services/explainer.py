"""Servicio Explainer: convierte el resultado del modelo en texto legible.

v0: la salida se centra en resultado, marcador y over/under, con una **única**
estimación de goles esperados (las λ de Dixon-Coles). Posesión, xG y tarjetas
quedan fuera del v0.
"""

from __future__ import annotations

from dataclasses import dataclass

from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.models.dixon_coles import MatchProbabilities


def _pct(p: float) -> str:
    """Formatea una probabilidad; nunca muestra 0.0% (en fútbol nada es imposible)."""
    if p < 0.001:
        return "<0.1%"
    return f"{p:.1%}"


@dataclass(frozen=True, slots=True)
class Explainer:
    """Genera un informe textual del partido a partir de la salida de Dixon-Coles."""

    total_line: float = 2.5
    matrix_max_goals: int = 6

    def explain(self, match: Match, probabilities: MatchProbabilities) -> str:
        """Devuelve un informe multilínea con el desglose de la predicción."""
        home = match.home.name
        away = match.away.name
        outcome = self._headline(home, away, probabilities)
        score = probabilities.most_likely_score

        lines = [
            f"{home} vs {away}",
            f"Pronóstico: {outcome}",
            "",
            "Resultado (1X2):",
            f"  {home}: {_pct(probabilities.home_win)}",
            f"  Empate: {_pct(probabilities.draw)}",
            f"  {away}: {_pct(probabilities.away_win)}",
            f"Goles esperados: {probabilities.lambda_home:.2f} - {probabilities.lambda_away:.2f}",
            f"Marcador más probable: {score[0]}-{score[1]}",
            f"Over {self.total_line} goles: {_pct(probabilities.over(self.total_line))}",
            "",
            *self._score_matrix(match, probabilities),
        ]
        return "\n".join(lines)

    def _score_matrix(self, match: Match, probabilities: MatchProbabilities) -> list[str]:
        """Tabla de probabilidades por marcador: local en horizontal, visitante en vertical."""
        n = self.matrix_max_goals
        matrix = probabilities.score_matrix
        lines = [
            f"Matriz de marcador (%) — {match.home.name} → (horiz.), {match.away.name} ↓ (vert.):",
        ]
        header = "      " + "".join(f"{i:>7}" for i in range(n + 1))
        lines.append(header)
        for j in range(n + 1):  # visitante (filas)
            cells = "".join(f"{matrix[i, j] * 100:>7.1f}" for i in range(n + 1))
            lines.append(f"{j:>4}  {cells}")
        return lines

    @staticmethod
    def _headline(home: str, away: str, probabilities: MatchProbabilities) -> str:
        options = {
            home: probabilities.home_win,
            "Empate": probabilities.draw,
            away: probabilities.away_win,
        }
        winner = max(options, key=lambda k: options[k])
        return f"{winner} ({_pct(options[winner])})"
