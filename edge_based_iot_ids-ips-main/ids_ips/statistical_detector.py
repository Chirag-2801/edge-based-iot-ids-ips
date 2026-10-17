import numpy as np

class StatisticalDetector:

    def __init__(self):
        self.baseline_rates = []

    def train_baseline(self, rate):
        self.baseline_rates.append(rate)

    def detect(self, rate):

        if len(self.baseline_rates) < 10:
            self.train_baseline(rate)
            return "LEARNING"

        mu = np.mean(self.baseline_rates)
        sigma = np.std(self.baseline_rates)

        z_score = (rate - mu) / sigma if sigma > 0 else 0

        if z_score > 3:
            return "ATTACK"
        elif z_score > 2:
            return "SUSPICIOUS"
        else:
            return "NORMAL"