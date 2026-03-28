import numpy as np
import pytest
from pathlib import Path
from astropy import units as u
from WeatherRoutingTool.config import Config
from WeatherRoutingTool.ship.ship_config import ShipConfig
from WeatherRoutingTool.ship.ship_factory import ShipFactory
from WeatherRoutingTool.weather_factory import WeatherFactory
from WeatherRoutingTool.constraints.constraints import ConstraintsListFactory
from WeatherRoutingTool.utils.maps import Map
from WeatherRoutingTool.algorithms.genetic.problem import RoutingProblem
from WeatherRoutingTool.algorithms.genetic.crossover import TwoPointCrossover, SinglePointCrossover


# ── shared fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def config():
    return Config.assign_config(str(Path(__file__).parent.parent / 'config.json'))

@pytest.fixture(scope="module")
def ship_config():
    return ShipConfig.assign_config(str(Path(__file__).parent.parent / 'config.json'))

@pytest.fixture(scope="module")
def default_map(config):
    lat1, lon1, lat2, lon2 = config.DEFAULT_MAP
    return Map(lat1, lon1, lat2, lon2)

@pytest.fixture(scope="module")
def boat(config, ship_config):
    return ShipFactory.get_ship(config.BOAT_TYPE, ship_config)

@pytest.fixture(scope="module")
def constraint_list(config, boat, default_map):
    return ConstraintsListFactory.get_constraints_list(
        constraints_string_list=config.CONSTRAINTS_LIST,
        data_mode=config._DATA_MODE_DEPTH,
        min_depth=boat.get_required_water_depth(),
        map_size=default_map,
        depthfile=config.DEPTH_DATA,
        waypoints=config.INTERMEDIATE_WAYPOINTS,
        courses_path=config.COURSES_FILE
    )

@pytest.fixture(scope="module")
def routing_problem(config, boat, constraint_list):
    return RoutingProblem(
        departure_time=config.DEPARTURE_TIME,
        arrival_time=config.ARRIVAL_TIME,
        boat=boat,
        boat_speed=config.BOAT_SPEED * u.meter / u.second,
        constraint_list=constraint_list
    )

@pytest.fixture(scope="module")
def dummy_route():
    return np.array([
        [10.0, 20.0, 3.09],
        [10.2, 20.2, 3.09],
        [10.4, 20.4, 3.09],
        [10.7, 20.7, 3.09]
    ])

@pytest.fixture(scope="module")
def route_result(routing_problem, dummy_route):
    fuel, ship_params = routing_problem.get_power(dummy_route)
    return fuel, ship_params


# ── TestGetPower ─────────────────────────────────────────────────────────────

class TestGetPower:

    def test_fuel_is_positive(self, route_result):
        """Total fuel consumption must be strictly positive."""
        fuel, _ = route_result
        assert fuel > 0, f"Expected positive fuel, got {fuel}"

    def test_fuel_has_mass_units(self, route_result):
        """Fuel must be returned in kg (SI mass unit)."""
        fuel, _ = route_result
        assert str(fuel.unit) == "kg", f"Expected kg, got {fuel.unit}"

    def test_fuel_rate_positive_per_segment(self, route_result):
        """Fuel rate must be positive for every segment."""
        _, ship_params = route_result
        fuel_rate = ship_params.get_fuel_rate()
        assert np.all(fuel_rate.value > 0), f"Fuel rate not positive: {fuel_rate}"

    def test_speed_matches_input(self, route_result):
        """Speed in ShipParams must match the input route speed (3.09 m/s)."""
        _, ship_params = route_result
        speed = ship_params.get_speed()
        np.testing.assert_allclose(
            speed.value, 3.09,
            rtol=1e-3,
            err_msg=f"Expected speed 3.09 m/s, got {speed}"
        )

    def test_wind_resistance_non_negative(self, route_result):
        """Wind resistance must be >= 0 for all waypoints."""
        _, ship_params = route_result
        rwind = ship_params.get_rwind()
        assert np.all(rwind.value >= 0), f"Negative wind resistance: {rwind}"

    def test_wave_height_reflects_weather_data(self, route_result):
        """Wave height in ShipParams must be within physical range of synthetic data."""
        _, ship_params = route_result
        wave_height = ship_params.get_wave_height()
        assert np.all(wave_height.value >= 0), "Negative wave height"
        assert np.all(wave_height.value < 20), "Unrealistically large wave height"

    def test_determinism(self, routing_problem, dummy_route):
        """get_power must return identical results on repeated calls (deterministic)."""
        fuel1, params1 = routing_problem.get_power(dummy_route)
        fuel2, params2 = routing_problem.get_power(dummy_route)
        assert fuel1 == fuel2, f"Non-deterministic fuel: {fuel1} vs {fuel2}"
        np.testing.assert_array_equal(
            params1.get_speed().value,
            params2.get_speed().value
        )

    def test_number_of_segments(self, route_result, dummy_route):
        """ShipParams must contain n-1 segments for n waypoints."""
        _, ship_params = route_result
        n_waypoints = dummy_route.shape[0]
        speed = ship_params.get_speed()
        assert len(speed) == n_waypoints - 1, (
            f"Expected {n_waypoints - 1} segments, got {len(speed)}"
        )


# ── TestCrossoverSafetyGuards ─────────────────────────────────────────────────

class TestCrossoverSafetyGuards:
    """
    Tests for the safety guards added to fix ValueError: low >= high.
    These guards were introduced during the GSoC code challenge when routes
    with too few points caused np.random.randint to crash.
    """

    def test_two_point_crossover_short_route_returns_parents(self, config, constraint_list):
        """TwoPointCrossover must return parents unchanged when route has < 6 points."""
        crossover = TwoPointCrossover(config=config, departure_time=config.DEPARTURE_TIME, constraints_list=constraint_list)
        short_route = np.array([
            [10.0, 20.0, 3.09],
            [10.3, 20.3, 3.09],
            [10.7, 20.7, 3.09]
        ])
        r1, r2 = crossover.crossover(short_route.copy(), short_route.copy())
        np.testing.assert_array_equal(r1, short_route)
        np.testing.assert_array_equal(r2, short_route)

    def test_single_point_crossover_short_route_returns_parents(self, config, constraint_list):
        """SinglePointCrossover must return parents unchanged when route has < 3 points."""
        crossover = SinglePointCrossover(config=config, departure_time=config.DEPARTURE_TIME, constraints_list=constraint_list)
        short_route = np.array([
            [10.0, 20.0, 3.09],
            [10.7, 20.7, 3.09]
        ])
        r1, r2 = crossover.crossover(short_route.copy(), short_route.copy())
        np.testing.assert_array_equal(r1, short_route)
        np.testing.assert_array_equal(r2, short_route)

    def test_two_point_crossover_valid_route_does_not_crash(self, config, constraint_list):
        """TwoPointCrossover must not crash when route has >= 6 points."""
        crossover = TwoPointCrossover(config=config, departure_time=config.DEPARTURE_TIME, constraints_list=constraint_list)
        valid_route = np.array([
            [10.0, 20.0, 3.09],
            [10.1, 20.1, 3.09],
            [10.2, 20.2, 3.09],
            [10.4, 20.4, 3.09],
            [10.6, 20.6, 3.09],
            [10.7, 20.7, 3.09]
        ])
        try:
            r1, r2 = crossover.crossover(valid_route.copy(), valid_route.copy())
            assert r1 is not None
            assert r2 is not None
        except ValueError as e:
            pytest.fail(f"TwoPointCrossover crashed on valid route: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
