"""Two-state linear Kalman filter for Health Index and degradation rate tracking."""

from dataclasses import dataclass

from purecast.domain.config import AlgorithmConfig


@dataclass
class KalmanState:
    """State vector [health, rate] and 2x2 covariance matrix."""

    health: float = 100.0
    rate: float = -0.2  # Daily rate of health change (negative when declining)
    p00: float = 1.0
    p01: float = 0.0
    p10: float = 0.0
    p11: float = 0.01

    def to_dict(self) -> dict[str, float]:
        return {
            "health": self.health,
            "rate": self.rate,
            "p00": self.p00,
            "p01": self.p01,
            "p10": self.p10,
            "p11": self.p11,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> "KalmanState":
        return cls(
            health=float(d.get("health", 100.0)),  # type: ignore[arg-type]
            rate=float(d.get("rate", -0.2)),  # type: ignore[arg-type]
            p00=float(d.get("p00", 1.0)),  # type: ignore[arg-type]
            p01=float(d.get("p01", 0.0)),  # type: ignore[arg-type]
            p10=float(d.get("p10", 0.0)),  # type: ignore[arg-type]
            p11=float(d.get("p11", 0.01)),  # type: ignore[arg-type]
        )


class TwoStateKalmanFilter:
    """Constant-velocity Kalman filter tracking health index and degradation rate.

    State vector: x = [health_index, rate_per_day]
    Process model:
        health(t + dt) = health(t) + rate(t) * dt
        rate(t + dt)   = rate(t)
    """

    def __init__(
        self,
        config: AlgorithmConfig | None = None,
        initial_state: KalmanState | None = None,
    ) -> None:
        cfg = config or AlgorithmConfig()
        self.state = initial_state or KalmanState(
            health=100.0,
            rate=-0.2,
            p00=cfg.kalman_initial_p_health,
            p11=cfg.kalman_initial_p_rate,
        )
        self.q_health = cfg.kalman_q_health
        self.q_rate = cfg.kalman_q_rate
        self.r_meas = cfg.kalman_r_meas

    def predict(self, dt_days: float) -> KalmanState:
        """Project state and covariance forward by dt_days."""
        dt = max(0.0, dt_days)
        # Predict state vector forward: x_pred = F @ x
        h_pred = self.state.health + self.state.rate * dt
        r_pred = self.state.rate

        # Predict covariance matrix forward: P_pred = F @ P @ F.T + Q
        p00 = (
            self.state.p00
            + dt * self.state.p10
            + dt * (self.state.p01 + dt * self.state.p11)
            + self.q_health
        )
        p01 = self.state.p01 + dt * self.state.p11
        p10 = self.state.p10 + dt * self.state.p11
        p11 = self.state.p11 + self.q_rate

        self.state.health = h_pred
        self.state.rate = r_pred
        self.state.p00 = p00
        self.state.p01 = p01
        self.state.p10 = p10
        self.state.p11 = p11
        return self.state

    def update(self, measured_health: float) -> KalmanState:
        """Incorporate a new health measurement using 2x2 matrix equations."""
        # Innovation
        y = measured_health - self.state.health

        # Innovation covariance S = H * P * H^T + R = p00 + R
        s = self.state.p00 + self.r_meas

        # Kalman gain K = P * H^T / S = [p00/S, p10/S]
        k0 = self.state.p00 / s
        k1 = self.state.p10 / s

        # State update x = x + K * y
        self.state.health += k0 * y
        self.state.rate += k1 * y

        # Covariance update P = (I - K * H) * P
        p00 = self.state.p00 - k0 * self.state.p00
        p01 = self.state.p01 - k0 * self.state.p01
        p10 = self.state.p10 - k1 * self.state.p00
        p11 = self.state.p11 - k1 * self.state.p01

        self.state.p00 = max(1e-9, p00)
        self.state.p01 = p01
        self.state.p10 = p10
        self.state.p11 = max(1e-9, p11)
        return self.state
