from fastapi import APIRouter, Depends

from app.config import get_settings
from app.services.power_control import Link, run_power_control

router = APIRouter(prefix="/power-control", tags=["power-control"])


@router.get("/simulate")
def simulate_power_control(n_links: int = 4, settings=Depends(get_settings)):
    """
    Run a small illustrative power-control convergence simulation for
    `n_links` co-channel links with a fixed, hand-picked interference
    topology, and return each link's convergence trajectory.
    """
    import numpy as np
    rng = np.random.default_rng(7)

    links = []
    for i in range(n_links):
        gain_own = 10 ** (rng.uniform(-9, -7))
        gains_other = [10 ** (rng.uniform(-12, -10)) for _ in range(n_links - 1)]
        links.append(Link(link_id=f"link-{i+1}", gain_to_own_receiver=gain_own, gains_to_other_receivers=gains_other))

    history = run_power_control(
        links,
        target_sinr_db=settings.power_control_target_sinr_db,
        max_iterations=settings.power_control_max_iterations,
        max_tx_power_dbm=settings.power_control_max_tx_power_dbm,
    )

    return {
        "target_sinr_db": settings.power_control_target_sinr_db,
        "links": {states[0].link_id: [s.model_dump() for s in states] for states in history},
    }
