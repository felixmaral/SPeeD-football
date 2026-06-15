"""Servicio Explainer: convierte los resultados de los modelos en texto legible."""

from __future__ import annotations

from dataclasses import dataclass

from wcpredictor.domain.entities.match import Match
from wcpredictor.domain.models.cards import CardsPrediction
from wcpredictor.domain.models.dixon_coles import MatchProbabilities
from wcpredictor.domain.models.performance import MatchPerformance


@dataclass(frozen=True, slots=True)
class Explainer:
    """Genera un informe textual del partido a partir de las salidas de los modelos.

    `total_line` y `cards_line` son las líneas de over/under para goles y tarjetas.
    """

    total_line: float = 2.5
    cards_line: float = 4.5

    def explain(
        self,
        match: Match,
        probabilities: MatchProbabilities,
        cards: CardsPrediction,
        performance: MatchPerformance,
    ) -> str:
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
            f"  {home}: {probabilities.home_win:.1%}",
            f"  Empate: {probabilities.draw:.1%}",
            f"  {away}: {probabilities.away_win:.1%}",
            f"Goles esperados: {probabilities.lambda_home:.2f} - {probabilities.lambda_away:.2f}",
            f"Marcador más probable: {score[0]}-{score[1]}",
            f"Over {self.total_line} goles: {probabilities.over(self.total_line):.1%}",
            "",
            "Tarjetas:",
            f"  Esperadas: {cards.expected_cards:.1f}",
            f"  Over {self.cards_line}: {cards.over(self.cards_line):.1%}",
            "",
            "Rendimiento:",
            f"  Posesión: {performance.home.possession:.0f}% - {performance.away.possession:.0f}%",
            f"  xG: {performance.home.xg:.2f} - {performance.away.xg:.2f}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _headline(home: str, away: str, probabilities: MatchProbabilities) -> str:
        options = {
            home: probabilities.home_win,
            "Empate": probabilities.draw,
            away: probabilities.away_win,
        }
        winner = max(options, key=lambda k: options[k])
        return f"{winner} ({options[winner]:.1%})"
