# car-repair-simulation

This project simulates a car repair queue system, where cars arrive at a garage, wait in a queue for repair, and are processed by mechanics with varying efficiency. The simulation uses **asynchronous programming** with Python's `asyncio` to manage concurrent tasks (such as car arrivals and mechanic work) in a realistic manner.

## Project Overview

- **Car Queue**: Cars arrive and are added to a priority-based queue. Each car has a priority (Low, Medium, or High), which affects how quickly it gets processed by the mechanic.
- **Mechanics**: Two mechanics work on the cars simultaneously. Each mechanic has a different efficiency, which affects how long it takes to repair a car.
- **Simulation**: The simulation enqueues cars, lets them wait in the queue, and assigns them to mechanics. After repairs, cars leave the system.

## Features

- **Queue Handling**: Cars are processed in the order of their priority, with higher-priority cars getting repaired faster.
- **Asynchronous Simulation**: Utilizes Python's `asyncio` to handle multiple tasks concurrently, simulating real-time car repairs.
- **Data Visualization**: After the simulation runs, several plots are generated to visualize the results, including:
    - Time spent in queue by each car.
    - Distribution of queue times based on car priority.
    - Gantt chart showing the mechanics' work timeline.

## Requirements

- Python 3.x
- `matplotlib` for data visualization

## Additional Authors

Huge thanks for contributions for: 
- @ttarnawski
- @Mountaineye
