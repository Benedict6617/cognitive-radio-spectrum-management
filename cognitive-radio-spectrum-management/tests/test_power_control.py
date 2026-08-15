from app.services.power_control import Link, run_power_control


def _two_link_topology():
    # weak mutual interference so the loop should converge comfortably
    return [
        Link(link_id="a", gain_to_own_receiver=1e-8, gains_to_other_receivers=[1e-11]),
        Link(link_id="b", gain_to_own_receiver=1e-8, gains_to_other_receivers=[1e-11]),
    ]


def test_power_control_converges_to_target_sinr():
    links = _two_link_topology()
    history = run_power_control(links, target_sinr_db=10.0, max_iterations=50, max_tx_power_dbm=30.0)

    for link_history in history:
        final_state = link_history[-1]
        assert final_state.converged is True
        assert abs(final_state.achieved_sinr_db - 10.0) < 1.0


def test_power_control_respects_max_tx_power():
    links = _two_link_topology()
    history = run_power_control(links, target_sinr_db=10.0, max_iterations=50, max_tx_power_dbm=5.0)

    for link_history in history:
        for state in link_history:
            assert state.tx_power_dbm <= 5.0 + 1e-6


def test_power_control_history_has_one_entry_per_iteration_per_link():
    links = _two_link_topology()
    history = run_power_control(links, target_sinr_db=10.0, max_iterations=50, max_tx_power_dbm=30.0)
    for link_history in history:
        assert len(link_history) == link_history[-1].iteration
