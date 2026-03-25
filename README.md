# 52°North Weather Routing Tool - GSoC 2026 Code Challenge

**Student:** Aakriti Jha
**GitHub:** aakritithecoder
**Project:** Weather Routing Tool - Improve Test Framework

---

## What I Did

### 1. Ran the WRT
Successfully ran the Weather Routing Tool using:
- ALGORITHM_TYPE: genetic
- BOAT_TYPE: direct_power_method

### 2. Synthetic Weather Data
Created 90 hours of synthetic weather data with all 11 required variables:
- Wind (U/V components)
- Wave height, direction, period (VHM0, VMDR, VTPK)
- Pressure, temperature
- Ocean currents, salinity, water temperature

### 3. Configuration
Full config.json with genetic algorithm, direct power method, and 7 intermediate waypoints.

### 4. Unit Test
Implemented test_routing_problem.py testing RoutingProblem.get_power:
- 1 passed in 6.29s

### 5. Route Output
Generated output/min_fuel_route.json:
- Route: (10.0, 20.0) to (10.7, 20.7)
- Best fuel: 7979.01 kg
- Travel time: ~9.8 hours
- Engine power: 4877.8 kW

---

## Bugs Fixed During the Process

| Bug | Fix |
|-----|-----|
| ValueError: low >= high in TwoPointCrossover | Added safety guard for route length |
| ValueError: low >= high in SinglePointCrossover | Added safety guard |
| AttributeError: NoneType has no attribute argmin | Added res.F is None check |
| TypeError: WindowsPath + str | Fixed with str(routepath) |
| FileNotFoundError on output write | Added os.makedirs |

---

## Files
- config.json - WRT configuration
- generate_90h_weather.py - synthetic weather data generator
- convert_csv_to_nc.py - CSV to NetCDF converter
- test_routing_problem.py - unit test for RoutingProblem.get_power
- min_fuel_route.json - generated route output
