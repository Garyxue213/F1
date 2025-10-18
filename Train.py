#!/usr/bin/env python3
"""
Simple DQN training script on a toy F1-like 2-lane simulator with 3 cars (you control 1).
- Discrete actions: throttle up, throttle down, keep speed, change lane left, change lane right
- Objective: make progress, safely overtake scripted opponents, avoid collisions

Dependencies: Python 3.9+, numpy, torch

Run:
  pip install numpy torch
  python train.py

Notes:
- This is a tiny, self-contained environment (no Gym needed) designed for hackathon demos.
- Tweak hyperparameters at the bottom under "CONFIG" to trade speed vs quality.
"""
import math
import random
import time
from dataclasses import dataclass
from typing import Tuple, List

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# ==========================
# Environment
# ==========================

@dataclass
class Car:
    pos: float         # position along the track [m]
    speed: float       # forward speed [m/s]
    lane: int          # 0 or 1

class SimpleF1Env:
    """A minimal 2-lane, 1D track environment with simple longitudinal dynamics.

    State (8-dim float32):
      [ agent_speed/VMAX,
        agent_lane (0 or 1),
        dist_ahead_same/LOOK,
        rel_speed_ahead_same/VMAX,
        dist_ahead_other/LOOK,
        rel_speed_ahead_other/VMAX,
        dist_behind_same/LOOK,
        dist_behind_other/LOOK ]

    Distances are clipped to [0, LOOK] and normalized by LOOK.

    Actions (5):
      0: throttle up (+ACC)
      1: throttle down (-ACC)
      2: maintain (0)
      3: change lane left (lane-1)
      4: change lane right (lane+1)

    Reward:
      + progress_gain = (delta_pos / LOOK) * PROGRESS_R
      + overtake_bonus when you pass another car
      - collision_penalty on crash -> episode ends
      - small lane change penalty
    """

    DT = 0.1          # seconds per step
    TRACK_LEN = 1000  # meters for a lap (wrap-around)
    VMAX = 80.0       # m/s (~288 km/h)
    ACC = 6.0         # m/s^2 accel magnitude
    LOOK = 200.0      # look-ahead/behind window [m]
    SAFE_GAP = 5.0    # meters; crash if closer

    PROGRESS_R = 5.0
    OVERTAKE_B = 2.0
    COLLISION_P = -20.0
    LANE_COST = -0.05

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.n_actions = 5
        self.state_dim = 8
        self.reset()

    def reset(self) -> np.ndarray:
        # Agent starts at lane 0, mid speed
        self.agent = Car(pos=0.0, speed=40.0 + self.rng.uniform(-5, 5), lane=0)
        # Two scripted opponents placed ahead with constant speeds & lanes
        # You can tune these for variety
        self.opponents: List[Car] = [
            Car(pos=120.0, speed=55.0, lane=0),
            Car(pos=220.0, speed=50.0, lane=1),
        ]
        self.prev_overtakes = 0
        self.t = 0
        return self._get_obs()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        assert 0 <= action < self.n_actions
        done = False
        info = {}

        # 1) Apply control
        acc = 0.0
        lane_change = False
        if action == 0:
            acc = self.ACC
        elif action == 1:
            acc = -self.ACC
        elif action == 2:
            acc = 0.0
        elif action == 3 and self.agent.lane > 0:
            self.agent.lane -= 1
            lane_change = True
        elif action == 4 and self.agent.lane < 1:
            self.agent.lane += 1
            lane_change = True

        # 2) Update kinematics
        self.agent.speed = float(np.clip(self.agent.speed + acc * self.DT, 0.0, self.VMAX))
        delta_pos = self.agent.speed * self.DT
        self.agent.pos = (self.agent.pos + delta_pos) % self.TRACK_LEN

        # Opponents move (scripted constant speeds, optional tiny noise)
        for c in self.opponents:
            c.pos = (c.pos + c.speed * self.DT) % self.TRACK_LEN

        # 3) Compute reward components
        reward = (delta_pos / self.LOOK) * self.PROGRESS_R
        if lane_change:
            reward += self.LANE_COST

        # Overtake detection: count how many cars are now behind that were ahead
        overtakes = 0
        for c in self.opponents:
            if self._is_ahead(c.pos, self.agent.pos):
                pass
            else:
                # This opponent is behind agent
                overtakes += 1
        if overtakes > self.prev_overtakes:
            reward += self.OVERTAKE_B * (overtakes - self.prev_overtakes)
        self.prev_overtakes = overtakes

        # 4) Collision check (same lane & too close front/back)
        collided = self._collision()
        if collided:
            reward += self.COLLISION_P
            done = True
            info["event"] = "collision"

        # 5) Episode timeout
        self.t += 1
        if self.t >= int(60 / self.DT):  # 60 seconds max
            done = True
            info["event"] = info.get("event", "timeout")

        return self._get_obs(), reward, done, info

    # ======= Helpers =======
    def _wrap_dist(self, a: float, b: float) -> float:
        """Forward distance from a -> b along the track (non-negative)."""
        d = (b - a) % self.TRACK_LEN
        return d

    def _is_ahead(self, other_pos: float, my_pos: float) -> bool:
        d = self._wrap_dist(my_pos, other_pos)
        return 0 < d < self.TRACK_LEN / 2

    def _nearest_in_lane(self, lane: int, ahead: bool) -> Tuple[float, float]:
        """Return (dist, rel_speed) to nearest car in a lane (ahead or behind). If none within LOOK, returns (LOOK, 0)."""
        best_d = self.LOOK
        best_rel_v = 0.0
        for c in self.opponents:
            if c.lane != lane:
                continue
            if ahead:
                d = self._wrap_dist(self.agent.pos, c.pos)
                if 0 < d < best_d:
                    best_d = d
                    best_rel_v = c.speed - self.agent.speed
            else:
                d = self._wrap_dist(c.pos, self.agent.pos)
                if 0 < d < best_d:
                    best_d = d
                    best_rel_v = self.agent.speed - c.speed
        return best_d, best_rel_v

    def _collision(self) -> bool:
        for c in self.opponents:
            if c.lane != self.agent.lane:
                continue
            # shortest absolute distance on ring
            d = abs(((c.pos - self.agent.pos + self.TRACK_LEN/2) % self.TRACK_LEN) - self.TRACK_LEN/2)
            if d < self.SAFE_GAP:
                return True
        return False

    def _get_obs(self) -> np.ndarray:
        lane = self.agent.lane
        d_same_a, rv_same_a = self._nearest_in_lane(lane, ahead=True)
        d_same_b, rv_same_b = self._nearest_in_lane(lane, ahead=False)
        other_lane = 1 - lane
        d_other_a, rv_other_a = self._nearest_in_lane(other_lane, ahead=True)
        d_other_b, rv_other_b = self._nearest_in_lane(other_lane, ahead=False)

        obs = np.array([
            self.agent.speed / self.VMAX,
            float(lane),
            min(d_same_a, self.LOOK) / self.LOOK,
            np.clip(rv_same_a / self.VMAX, -1.0, 1.0),
            min(d_other_a, self.LOOK) / self.LOOK,
            np.clip(rv_other_a / self.VMAX, -1.0, 1.0),
            min(d_same_b, self.LOOK) / self.LOOK,
            min(d_other_b, self.LOOK) / self.LOOK,
        ], dtype=np.float32)
        return obs

# ==========================
# DQN Agent
# ==========================

class QNet(nn.Module):
    def __init__(self, state_dim: int, n_actions: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU(),
            nn.Linear(128, n_actions),
        )
    def forward(self, x):
        return self.net(x)

class ReplayBuffer:
    def __init__(self, capacity: int, state_dim: int):
        self.capacity = capacity
        self.state = np.zeros((capacity, state_dim), dtype=np.float32)
        self.action = np.zeros((capacity,), dtype=np.int64)
        self.reward = np.zeros((capacity,), dtype=np.float32)
        self.next_state = np.zeros((capacity, state_dim), dtype=np.float32)
        self.done = np.zeros((capacity,), dtype=np.float32)
        self.ptr = 0
        self.full = False
    def push(self, s, a, r, ns, d):
        i = self.ptr
        self.state[i] = s
        self.action[i] = a
        self.reward[i] = r
        self.next_state[i] = ns
        self.done[i] = d
        self.ptr = (self.ptr + 1) % self.capacity
        if self.ptr == 0:
            self.full = True
    def sample(self, batch_size: int):
        hi = self.capacity if self.full else self.ptr
        idx = np.random.randint(0, hi, size=batch_size)
        return (
            torch.from_numpy(self.state[idx]),
            torch.from_numpy(self.action[idx]),
            torch.from_numpy(self.reward[idx]),
            torch.from_numpy(self.next_state[idx]),
            torch.from_numpy(self.done[idx]),
        )
    def __len__(self):
        return self.capacity if self.full else self.ptr

# ==========================
# Training Loop
# ==========================

def train(seed: int = 42):
    # ----- CONFIG -----
    EPISODES = 200            # increase for better policy
    STEPS_PER_EP = 600        # upper bound; env may end earlier
    START_EPS = 1.0           # epsilon-greedy start
    END_EPS = 0.05            # epsilon-greedy end
    EPS_DECAY = 0.995         # per-episode decay
    BATCH = 64
    GAMMA = 0.99
    LR = 1e-3
    TARGET_SYNC = 200         # steps between target net syncs
    REPLAY_CAP = 50000
    WARMUP = 1000             # steps before learning starts
    SAVE_PATH = "f1_dqn.pt"

    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)

    env = SimpleF1Env(seed=seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    q = QNet(env.state_dim, env.n_actions).to(device)
    q_target = QNet(env.state_dim, env.n_actions).to(device)
    q_target.load_state_dict(q.state_dict())
    opt = optim.Adam(q.parameters(), lr=LR)

    rb = ReplayBuffer(REPLAY_CAP, env.state_dim)

    epsilon = START_EPS
    global_step = 0

    def act(state: np.ndarray) -> int:
        nonlocal epsilon
        if np.random.rand() < epsilon:
            return np.random.randint(env.n_actions)
        with torch.no_grad():
            s = torch.from_numpy(state).unsqueeze(0).to(device)
            qv = q(s)
            return int(torch.argmax(qv, dim=1).item())

    losses = []
    best_mean = -1e9

    for ep in range(1, EPISODES + 1):
        s = env.reset()
        ep_ret = 0.0
        for t in range(STEPS_PER_EP):
            a = act(s)
            ns, r, done, info = env.step(a)
            rb.push(s, a, r, ns, float(done))
            s = ns
            ep_ret += r
            global_step += 1

            # learn
            if len(rb) > WARMUP:
                S, A, R, NS, D = rb.sample(BATCH)
                S = S.to(device); A = A.to(device); R = R.to(device); NS = NS.to(device); D = D.to(device)

                with torch.no_grad():
                    # Double DQN
                    next_actions = torch.argmax(q(NS), dim=1, keepdim=True)
                    q_next = q_target(NS).gather(1, next_actions).squeeze(1)
                    target = R + GAMMA * (1.0 - D) * q_next

                q_pred = q(S).gather(1, A.view(-1,1)).squeeze(1)
                loss = nn.functional.smooth_l1_loss(q_pred, target)
                opt.zero_grad(); loss.backward(); opt.step()
                losses.append(loss.item())

                # target sync
                if global_step % TARGET_SYNC == 0:
                    q_target.load_state_dict(q.state_dict())

            if done:
                break

        # epsilon decay per episode
        epsilon = max(END_EPS, epsilon * EPS_DECAY)

        # logging
        if ep % 10 == 0 or ep == 1:
            mean_loss = float(np.mean(losses[-100:])) if losses else 0.0
            print(f"Ep {ep:4d} | return {ep_ret:7.3f} | eps {epsilon:5.3f} | mean_loss {mean_loss:7.4f}")

        # checkpoint best average every 20 eps (quick heuristic)
        if ep % 20 == 0:
            window = 20
            # not storing rets per ep; quick re-run of last ep_ret is fine for demo
            # For more rigorous tracking, keep a list of returns.
            if ep_ret > best_mean:
                best_mean = ep_ret
                torch.save(q.state_dict(), SAVE_PATH)

    # Final save
    torch.save(q.state_dict(), SAVE_PATH)
    print(f"Saved model to {SAVE_PATH}")


if __name__ == "__main__":
    train()


