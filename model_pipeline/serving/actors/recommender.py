import numpy as np

class ChampionRecommender:
    def __init__(self, relations: dict):
        """
        Args:
            relations (ChampionRelationsEfficient): precomputed synergy and counter matrices.
        """
        self.Ts = relations["Ts"]
        self.Tc = relations["Tc"]
        self.synergy_matrix = relations["synergy_matrix"]
        self.counter_matrix = relations["counter_matrix"]
        self.champion_index = relations["champion_index"]
        print(self.Ts, self.Tc, self.synergy_matrix, self.counter_matrix, self.champion_index)

    def recommend_weighted(self, allies: list[str], opponents: list[str], bans: list[str] = None, top_n: int = 5):
        """
        Recommend top N champions based on weighted average of synergy and counter scores.

        Args:
            allies (list[str]): Current allied champions
            opponents (list[str]): Current enemy champions
            bans (list[str]): Champions that cannot be picked
            top_n (int): Number of top champions to return

        Returns:
            list[tuple[str, float]]: List of (champion, score) sorted by score (desc)
        """
        if bans is None:
            bans = []

        synergy = self.synergy_matrix
        counter = self.counter_matrix
        Ts = self.Ts
        Tc = self.Tc
        idx = self.champion_index
        champions = self.champion_index  # all available champion names

        results = []

        for c in champions:
            if c in allies or c in opponents or c in bans:
                continue

            i = idx[c]

            synergy_weighted = sum(
                synergy[i][idx[a]] * Ts[i][idx[a]] for a in allies if Ts[i][idx[a]] > 0
            )
            counter_weighted = sum(
                counter[i][idx[o]] * Tc[i][idx[o]] for o in opponents if Tc[i][idx[o]] > 0
            )

            total_weight = sum(Ts[i][idx[a]] for a in allies) + sum(Tc[i][idx[o]] for o in opponents)

            if total_weight == 0:
                continue

            score = (synergy_weighted + counter_weighted) / total_weight
            results.append((c, score))

        # Sort by highest score and return top N
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]
