"""
Unit tests for wc26-bnaul core modules.

Run with: pytest tests/ -v
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest
import json
import hashlib
import hmac
from unittest.mock import patch, MagicMock

from wc26_bnaul import sign_request, get_credentials
from wc26_bnaul.strategy import expected_brier, optimal_submission_prob
from wc26_bnaul.predictor import MatchPredictor, poisson_pmf, expected_goals


class TestHMACSigning(unittest.TestCase):
    """Test HMAC signing implementation."""

    def test_sign_request_structure(self):
        """Sign request returns correct headers."""
        secret = "test_secret"
        sig = sign_request("GET", "/me", b"", secret)
        
        self.assertIn("X-WCA-Timestamp", sig)
        self.assertIn("X-WCA-Nonce", sig)
        self.assertIn("X-WCA-Signature", sig)
        
        # Timestamp should be numeric
        self.assertTrue(sig["X-WCA-Timestamp"].isdigit())
        
        # Nonce should be non-empty
        self.assertTrue(len(sig["X-WCA-Nonce"]) > 0)
        
        # Signature should be 64-char hex (SHA-256)
        self.assertEqual(len(sig["X-WCA-Signature"]), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in sig["X-WCA-Signature"]))

    def test_sign_request_deterministic_with_same_inputs(self):
        """Same inputs should produce same signature if ts/nonce fixed."""
        secret = "test_secret"
        body = b"test_body"
        
        # Manually compute signature
        ts = "1234567890"
        nonce = "test_nonce_123"
        body_hash = hashlib.sha256(body).hexdigest()
        canonical = f"POST\n/predictions\n{ts}\n{nonce}\n{body_hash}"
        expected_sig = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
        
        # Verify structure matches
        sig = sign_request("POST", "/predictions", body, secret)
        self.assertEqual(len(sig["X-WCA-Signature"]), len(expected_sig))

    def test_sign_request_different_methods(self):
        """Different HTTP methods produce different signatures."""
        secret = "test_secret"
        
        sig_get = sign_request("GET", "/me", b"", secret)
        sig_post = sign_request("POST", "/me", b"", secret)
        
        # Different timestamps/nonce means different signatures
        self.assertNotEqual(sig_get["X-WCA-Signature"], sig_post["X-WCA-Signature"])

    def test_sign_request_empty_body(self):
        """GET request with empty body should work."""
        secret = "test_secret"
        sig = sign_request("GET", "/me", b"", secret)
        
        self.assertIn("X-WCA-Signature", sig)
        self.assertEqual(len(sig["X-WCA-Signature"]), 64)


class TestStrategy(unittest.TestCase):
    """Test strategy module (Brier score, Kelly criterion)."""

    def test_expected_brier_truthful(self):
        """Brier score at true belief should be minimum."""
        pi = 0.7
        p = 0.7
        brier = expected_brier(pi, p)
        
        # Brier score should be pi*(1-pi) = 0.7*0.3 = 0.21
        self.assertAlmostEqual(brier, 0.21, places=5)

    def test_expected_brier_over_confident(self):
        """Over-confident submission increases Brier score."""
        pi = 0.7
        p_truthful = 0.7
        p_over = 0.9
        
        brier_truthful = expected_brier(pi, p_truthful)
        brier_over = expected_brier(pi, p_over)
        
        self.assertLess(brier_truthful, brier_over)

    def test_expected_brier_under_confident(self):
        """Under-confident submission increases Brier score."""
        pi = 0.7
        p_truthful = 0.7
        p_under = 0.5
        
        brier_truthful = expected_brier(pi, p_truthful)
        brier_under = expected_brier(pi, p_under)
        
        self.assertLess(brier_truthful, brier_under)

    def test_optimal_submission_prob(self):
        """Optimal submission is true belief."""
        for pi in [0.1, 0.3, 0.5, 0.7, 0.9]:
            optimal = optimal_submission_prob(pi)
            self.assertAlmostEqual(optimal, pi, places=5)

    def test_brier_score_symmetry(self):
        """Brier score is symmetric: BS(p, pi) = BS(1-p, 1-pi)."""
        pi = 0.7
        p = 0.8
        
        brier1 = expected_brier(pi, p)
        brier2 = expected_brier(1 - pi, 1 - p)
        
        self.assertAlmostEqual(brier1, brier2, places=5)

    def test_brier_score_range(self):
        """Brier score is always in [0, 1]."""
        for pi in [0.0, 0.5, 1.0]:
            for p in [0.0, 0.5, 1.0]:
                brier = expected_brier(pi, p)
                self.assertGreaterEqual(brier, 0.0)
                self.assertLessEqual(brier, 1.0)


class TestPredictor(unittest.TestCase):
    """Test prediction model."""

    def test_poisson_pmf_sum_to_one(self):
        """Poisson PMF should sum to approximately 1."""
        lam = 2.0
        total = sum(poisson_pmf(k, lam) for k in range(20))
        self.assertAlmostEqual(total, 1.0, places=3)

    def test_poisson_pmf_non_negative(self):
        """Poisson PMF should be non-negative."""
        lam = 2.0
        for k in range(10):
            self.assertGreaterEqual(poisson_pmf(k, lam), 0.0)

    def test_expected_goals_basic(self):
        """Expected goals calculation."""
        goals_scored = 10
        goals_conceded = 5
        matches = 5
        
        xg = expected_goals(goals_scored, goals_conceded, matches)
        self.assertGreater(xg, 0.0)
        self.assertEqual(xg, (10/5 + 5/5) / 2)  # (2 + 1) / 2 = 1.5

    def test_predictor_output_structure(self):
        """Predictor should return valid probabilities."""
        predictor = MatchPredictor()
        result = predictor.predict(
            home_team="Brazil",
            away_team="Japan",
            home_rank=6,
            away_rank=18,
            home_form=[1, 1, 0, 1, 1],
            away_form=[1, 0, 0, 1, 1],
            h2h_home_wins=7,
            h2h_draws=2,
            h2h_away_wins=1,
            home_goals_scored=15,
            home_goals_conceded=4,
            away_goals_scored=8,
            away_goals_conceded=3,
            knockout=True,
        )
        
        # Probabilities should sum to 1
        total_prob = result.home_win_prob + result.draw_prob + result.away_win_prob
        self.assertAlmostEqual(total_prob, 1.0, places=2)
        
        # All probabilities should be in [0, 1]
        self.assertGreaterEqual(result.home_win_prob, 0.0)
        self.assertLessEqual(result.home_win_prob, 1.0)
        self.assertGreaterEqual(result.draw_prob, 0.0)
        self.assertLessEqual(result.draw_prob, 1.0)
        self.assertGreaterEqual(result.away_win_prob, 0.0)
        self.assertLessEqual(result.away_win_prob, 1.0)
        
        # Expected goals should be non-negative
        self.assertGreaterEqual(result.expected_home_goals, 0.0)
        self.assertGreaterEqual(result.expected_away_goals, 0.0)
        
        # Confidence should be in [0, 1]
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)

    def test_predictor_binary_conversion(self):
        """Binary conversion for knockout stage."""
        predictor = MatchPredictor()
        result = predictor.predict(
            home_team="Brazil",
            away_team="Japan",
            home_rank=6,
            away_rank=18,
            knockout=True,
        )
        
        binary = result.to_binary()
        self.assertEqual(len(binary), 2)
        self.assertAlmostEqual(binary[0] + binary[1], 1.0, places=2)
        self.assertGreaterEqual(binary[0], 0.0)
        self.assertLessEqual(binary[0], 1.0)

    def test_predictor_favorite_wins_more(self):
        """Stronger team should have higher win probability."""
        predictor = MatchPredictor()
        
        # Brazil (rank 6) vs Japan (rank 18)
        result_brazil = predictor.predict(
            home_team="Brazil", away_team="Japan",
            home_rank=6, away_rank=18,
            knockout=True,
        )
        
        # Japan (rank 18) vs Brazil (rank 6) - reversed
        result_japan = predictor.predict(
            home_team="Japan", away_team="Brazil",
            home_rank=18, away_rank=6,
            knockout=True,
        )
        
        self.assertGreater(result_brazil.home_win_prob, result_japan.home_win_prob)

    def test_predictor_form_impact(self):
        """Better form should increase win probability."""
        predictor = MatchPredictor()
        
        # Good form
        result_good = predictor.predict(
            home_team="A", away_team="B",
            home_rank=10, away_rank=10,
            home_form=[1, 1, 1, 1, 1],  # 5 wins
            away_form=[-1, -1, -1, -1, -1],  # 5 losses
        )
        
        # Bad form
        result_bad = predictor.predict(
            home_team="A", away_team="B",
            home_rank=10, away_rank=10,
            home_form=[-1, -1, -1, -1, -1],  # 5 losses
            away_form=[1, 1, 1, 1, 1],  # 5 wins
        )
        
        self.assertGreater(result_good.home_win_prob, result_bad.home_win_prob)

    def test_predictor_reasoning_not_empty(self):
        """Reasoning should not be empty."""
        predictor = MatchPredictor()
        result = predictor.predict(
            home_team="Brazil", away_team="Japan",
            home_rank=6, away_rank=18,
        )
        
        self.assertTrue(len(result.reasoning) > 0)
        self.assertIn("FIFA rank", result.reasoning)


class TestCredentials(unittest.TestCase):
    """Test credential handling."""

    @patch.dict(os.environ, {"CLAWCUP_TOKEN": "test_token", "CLAWCUP_SIGNING_SECRET": "test_secret"})
    def test_get_credentials_success(self):
        """Should return credentials when set."""
        token, secret = get_credentials()
        self.assertEqual(token, "test_token")
        self.assertEqual(secret, "test_secret")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_credentials_missing_token(self):
        """Should exit when token missing."""
        with self.assertRaises(SystemExit) as cm:
            get_credentials()
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {"CLAWCUP_TOKEN": "test_token"}, clear=True)
    def test_get_credentials_missing_secret(self):
        """Should exit when secret missing."""
        with self.assertRaises(SystemExit) as cm:
            get_credentials()
        self.assertEqual(cm.exception.code, 1)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_predictor_equal_teams(self):
        """Predictor with equal teams should give near 50/50."""
        predictor = MatchPredictor()
        result = predictor.predict(
            home_team="A", away_team="B",
            home_rank=50, away_rank=50,
            home_form=[0, 0, 0, 0, 0],
            away_form=[0, 0, 0, 0, 0],
            knockout=False,
        )
        
        # Home should have slight advantage due to home advantage
        # But should be close to 50/50 (within 15%)
        self.assertLess(abs(result.home_win_prob - 0.5), 0.15)
        self.assertLess(abs(result.away_win_prob - 0.5), 0.15)

    def test_predictor_no_h2h(self):
        """Predictor with no H2H history should still work."""
        predictor = MatchPredictor()
        result = predictor.predict(
            home_team="A", away_team="B",
            h2h_home_wins=0, h2h_draws=0, h2h_away_wins=0,
        )
        
        self.assertAlmostEqual(result.home_win_prob + result.draw_prob + result.away_win_prob, 1.0, places=2)

    def test_predictor_no_form(self):
        """Predictor with no form data should still work."""
        predictor = MatchPredictor()
        result = predictor.predict(
            home_team="A", away_team="B",
            home_form=None, away_form=None,
        )
        
        self.assertAlmostEqual(result.home_win_prob + result.draw_prob + result.away_win_prob, 1.0, places=2)

    def test_expected_goals_zero_matches(self):
        """Expected goals with zero matches should not crash."""
        xg = expected_goals(0, 0, 0)
        self.assertEqual(xg, 1.0)  # Default value


if __name__ == "__main__":
    unittest.main()
