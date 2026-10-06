"""rl_router.py - RL Actor-Critic router for strategy selection.

Extends the UCB1 BanditRouter with a full Actor-Critic (A2C) policy network.

Architecture:
  State  = [context_features (8), recent_rewards (5), arm_stats (n_arms*3)]
  Actor  = 2-layer MLP → softmax over arms
  Critic = 2-layer MLP → scalar value estimate

Training: online, one gradient step per arm pull result.

Falls back to BanditRouter when torch is unavailable.

Reference:
  Sutton & Barto "Reinforcement Learning: An Introduction" (2020)
  Mnih et al. "Asynchronous Methods for Deep RL" (2016) — A3C actor-critic

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import math
import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from wfh_modules.bandit_router import ArmStats, BanditRouter


# ── Feature extraction ────────────────────────────────────────────────────────

def _arm_stats_features(arm: ArmStats) -> list[float]:
    """3 features per arm: mean_reward, n_pulls (log), confidence."""
    n = arm.n_pulls
    mean = arm.mean_reward
    conf = math.sqrt(2 * math.log(max(n + 1, 1)) / max(n, 1))
    return [mean, math.log1p(n) / 10.0, min(conf, 1.0)]


# ── Minimal neural A2C (pure Python) ─────────────────────────────────────────

class _Linear:
    """Single linear layer with kaiming init."""

    def __init__(self, in_f: int, out_f: int, rng: random.Random) -> None:
        scale = math.sqrt(2.0 / in_f)
        self.W = [[rng.gauss(0, scale) for _ in range(in_f)] for _ in range(out_f)]
        self.b = [0.0] * out_f

    def forward(self, x: list[float]) -> list[float]:
        return [
            self.b[i] + sum(self.W[i][j] * x[j] for j in range(len(x)))
            for i in range(len(self.b))
        ]

    def update(self, grad_out: list[float], x: list[float], lr: float) -> list[float]:
        grad_in = [0.0] * len(x)
        for i, g in enumerate(grad_out):
            self.b[i] -= lr * g
            for j in range(len(x)):
                self.W[i][j] -= lr * g * x[j]
                grad_in[j] += g * self.W[i][j]
        return grad_in


def _relu(x: list[float]) -> list[float]:
    return [max(0.0, v) for v in x]


def _relu_grad(x: list[float]) -> list[float]:
    return [1.0 if v > 0 else 0.0 for v in x]


def _softmax(x: list[float]) -> list[float]:
    m = max(x)
    exp = [math.exp(v - m) for v in x]
    z = sum(exp) or 1.0
    return [e / z for e in exp]


class _ActorCriticMLP:
    """Two-head MLP: actor (policy) + critic (value)."""

    def __init__(self, in_f: int, hidden: int, n_arms: int, rng: random.Random) -> None:
        self.l1 = _Linear(in_f, hidden, rng)
        self.actor_head = _Linear(hidden, n_arms, rng)
        self.critic_head = _Linear(hidden, 1, rng)

    def forward(self, x: list[float]) -> tuple[list[float], float]:
        h = _relu(self.l1.forward(x))
        probs = _softmax(self.actor_head.forward(h))
        value = self.critic_head.forward(h)[0]
        return probs, value

    def update(
        self,
        x: list[float],
        action: int,
        reward: float,
        lr: float,
        gamma: float = 0.95,
    ) -> None:
        h_raw = self.l1.forward(x)
        h = _relu(h_raw)

        probs, value = self.forward(x)
        advantage = reward - value

        # actor gradient: -log π(a) * advantage
        actor_logits = self.actor_head.forward(h)
        actor_grad = [p for p in probs]  # softmax grad trick
        actor_grad[action] -= 1.0
        actor_grad = [g * (-advantage) for g in actor_grad]
        dh_actor = self.actor_head.update(actor_grad, h, lr)

        # critic gradient: MSE
        critic_grad = [2.0 * (value - reward)]
        dh_critic = self.critic_head.update(critic_grad, h, lr)

        # backprop through hidden layer
        dh = [dh_actor[i] + dh_critic[i] for i in range(len(h))]
        dh_relu = [dh[i] * _relu_grad([h_raw[i]])[0] for i in range(len(h))]
        self.l1.update(dh_relu, x, lr)

    def save(self, path: str) -> None:
        data = {
            "l1_W": self.l1.W, "l1_b": self.l1.b,
            "actor_W": self.actor_head.W, "actor_b": self.actor_head.b,
            "critic_W": self.critic_head.W, "critic_b": self.critic_head.b,
        }
        Path(path).write_text(json.dumps(data), encoding="utf-8")

    def load(self, path: str) -> bool:
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            self.l1.W = d["l1_W"]; self.l1.b = d["l1_b"]
            self.actor_head.W = d["actor_W"]; self.actor_head.b = d["actor_b"]
            self.critic_head.W = d["critic_W"]; self.critic_head.b = d["critic_b"]
            return True
        except Exception:
            return False


# ── RLRouter ─────────────────────────────────────────────────────────────────

class RLRouter(BanditRouter):
    """Actor-Critic router extending BanditRouter.

    Uses a neural A2C policy when enough history is available (>= warmup_steps).
    Falls back to UCB1 during warm-up and when torch unavailable.
    """

    def __init__(
        self,
        arm_names: list[str],
        hidden: int = 64,
        lr: float = 0.01,
        warmup_steps: int = 30,
        seed: Optional[int] = None,
        model_path: Optional[str] = None,
    ) -> None:
        super().__init__(arm_names)
        n = len(arm_names)
        rng = random.Random(seed)
        # input = 8 context features + 5 recent rewards + n_arms*3
        self._in_f = 8 + 5 + n * 3
        self._n_arms = n
        self._model = _ActorCriticMLP(self._in_f, hidden, n, rng)
        self._lr = lr
        self._warmup = warmup_steps
        self._steps = 0
        self._recent_rewards: deque[float] = deque([0.0] * 5, maxlen=5)
        self._context_feat: list[float] = [0.0] * 8
        self._last_action: Optional[int] = None
        self._last_state: Optional[list[float]] = None
        if model_path and Path(model_path).exists():
            self._model.load(model_path)

    def set_context(self, feat: list[float]) -> None:
        """Provide 8-dimensional context feature vector."""
        self._context_feat = (feat + [0.0] * 8)[:8]

    def _build_state(self) -> list[float]:
        arm_feats: list[float] = []
        for name in self._arms:
            arm_feats.extend(_arm_stats_features(self._stats[name]))
        recent = list(self._recent_rewards)
        return self._context_feat + recent + arm_feats

    def select(self) -> str:
        if self._steps < self._warmup:
            return super().select()
        state = self._build_state()
        probs, _ = self._model.forward(state)
        # sample from policy
        r = random.random()
        cum = 0.0
        chosen_idx = 0
        for i, p in enumerate(probs):
            cum += p
            if r <= cum:
                chosen_idx = i
                break
        self._last_action = chosen_idx
        self._last_state = state
        return self._arms[chosen_idx]

    def update(self, arm_name: str, reward: float) -> None:
        super().update(arm_name, reward)
        self._recent_rewards.append(reward)
        self._steps += 1
        if self._steps >= self._warmup and self._last_action is not None and self._last_state is not None:
            self._model.update(self._last_state, self._last_action, reward, self._lr)

    def save(self, path: str) -> None:
        self._model.save(path)

    def load(self, path: str) -> bool:
        return self._model.load(path)

    def describe(self) -> str:
        base = super().describe()
        mode = "RL-policy" if self._steps >= self._warmup else f"UCB1 warm-up ({self._steps}/{self._warmup})"
        return f"{base}\n  Mode: {mode}"
