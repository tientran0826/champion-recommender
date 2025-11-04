import numpy as np

class ChampionRecommender:
    def __init__(self, relations):
        """
        Args:
            relations (ChampionRelationsEfficient): precomputed synergy and counter matrices.
        """
        self.relations = relations

    def recommend_weighted(self, allies, opponents, bans=None):
        """
        Implement Approach 2: Weighted average by sample size.

        Args:
            allies (list[str]): Current allied champions
            opponents (list[str]): Current enemy champions
            bans (list[str]): Champions that cannot be picked

        Returns:
            (str, float): Recommended champion and its score
        """
        if bans is None:
            bans = []

        synergy = self.relations.S
        counter = self.relations.C
        Ts = self.relations.Ts
        Tc = self.relations.Tc
        champions = self.relations.champions
        idx = self.relations.champ_index

        best_champ = None
        best_score = -np.inf

        for c in champions:
            if c in allies or c in opponents or c in bans:
                continue

            i = idx[c]

            # Weighted sum
            synergy_weighted = sum(
                synergy[i][idx[a]] * Ts[i][idx[a]] for a in allies if Ts[i][idx[a]] > 0
            )
            counter_weighted = sum(
                counter[i][idx[o]] * Tc[i][idx[o]] for o in opponents if Tc[i][idx[o]] > 0
            )

            # Denominator: total samples used
            total_weight = sum(Ts[i][idx[a]] for a in allies) + sum(Tc[i][idx[o]] for o in opponents)

            if total_weight == 0:
                continue

            score = (synergy_weighted + counter_weighted) / total_weight

            if score > best_score:
                best_score = score
                best_champ = c

        return best_champ, best_score
