import numpy as np
import itertools

class ChampionRelations:
    def __init__(self, raw_matches):
        """
        Initialize the ChampionRelations object.

        Args:
            matches (list): A list of tuples (team1, team2, team1_win)
        """
        self.matches = self.process_matches(raw_matches)
        # Build the full unique champion list
        champions = sorted({champ for t1, t2, _ in self.matches for champ in t1 + t2})
        self.champ_index = {c: i for i, c in enumerate(champions)}
        self.champions = champions

        # Initialize matrices
        size = len(champions)
        self.S = np.zeros((size, size), dtype=int)   # synergy wins
        self.Ts = np.zeros((size, size), dtype=int)  # synergy total
        self.C = np.zeros((size, size), dtype=int)   # counter wins
        self.Tc = np.zeros((size, size), dtype=int)  # counter total

    def process_matches(self, raw_matches):
        matches = []
        for match in raw_matches:
            team1 = match['team1_champions'].split(',')
            team2 = match['team2_champions'].split(',')
            win = match['team1_win'].lower() == 'true'
            matches.append((team1, team2, win))
        return matches

    def calculate(self):
        """Compute synergy and counter for all champion pairs."""
        for team1, team2, team1_win in self.matches:
            # Determine winner/loser teams
            cwinner, closer = (team1, team2) if team1_win else (team2, team1)

            # --- Synergy (same team) ---
            for team in [cwinner, closer]:
                for ca, cb in itertools.permutations(team, 2):
                    a, b = self.champ_index[ca], self.champ_index[cb]
                    self.Ts[a][b] += 1
                    if team == cwinner:
                        self.S[a][b] += 1

            # --- Counter (winner vs loser) ---
            for ca in cwinner:
                for cb in closer:
                    a, b = self.champ_index[ca], self.champ_index[cb]
                    self.C[a][b] += 1  # winner beats loser
                    self.Tc[a][b] += 1
            for ca in closer:
                for cb in cwinner:
                    a, b = self.champ_index[ca], self.champ_index[cb]
                    self.Tc[a][b] += 1  # total matchups

        # Compute normalized matrices
        synergy = np.divide(self.S, self.Ts, out=np.zeros_like(self.S, dtype=float), where=self.Ts != 0)
        counter = np.divide(self.C, self.Tc, out=np.zeros_like(self.C, dtype=float), where=self.Tc != 0)

        return synergy, counter

    def get_synergy(self, ci, cj, synergy_matrix):
        return synergy_matrix[self.champ_index[ci], self.champ_index[cj]]

    def get_counter(self, ci, cj, counter_matrix):
        return counter_matrix[self.champ_index[ci], self.champ_index[cj]]

    def get_champ_index(self):
        return self.champ_index

    def get_champions(self):
        return self.champions

    def get_champion_by_index(self, index):
        return self.champions[index]

    def get_ts_tc(self):
        return self.Ts, self.Tc
