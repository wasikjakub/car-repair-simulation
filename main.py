import asyncio
from asyncio import PriorityQueue
from random import randrange
from time import time
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

class Car:
    def __init__(self, id, repair_time, priority): 
        self.id = id
        self.repair_time = repair_time # time needed for mechanic to fix the car (dequeue)
        self.priority = priority # priority given in FIFO queue (0 priority being the lowest, then order)
        self.arrival_time = None # time when car arrived in queue (enqueued)
        self.repair_start_time = None # time when car started to be repaired
        self.spent_time = None # time spent in queue
        
    def set_arrival_time(self):
        self.arrival_time = time()    
        
    def set_queue_duration(self):
        self.repair_start_time = time()
        if self.repair_start_time is not None and self.arrival_time is not None:
            self.spent_time = self.repair_start_time - self.arrival_time
        
    def __lt__(self, other):
        return self.priority > other.priority
        
    @staticmethod
    async def enqueue_cars(queue, num_cars):
        for i in range(1, num_cars + 1):
            car = Car(i, randrange(1, 9), randrange(3))
            await queue.put(car)  # Enqueue as (priority, car)
            car.set_arrival_time()
            
            print(f"Car {car.id} with {car.priority} priority added to the queue.")
            
            await asyncio.sleep(0.25)  # Simulate time between cars arriving
        
        
class Mechanic:
    def __init__(self, id, efficiency, work_hours):
        self.id = id
        self.efficiency = efficiency
        self.work_hours = work_hours
        self.total_repairs = 0
        self.spent_times = []  # List to store the spent times for cars repaired by this mechanic

    async def repair(self, car):
        car.set_queue_duration()
        print(f"Mechanic {self.id} started repairing car {car.id} with {car.priority} priority. It will take {car.repair_time / self.efficiency} hours.")
        
        await asyncio.sleep(car.repair_time / self.efficiency)  # Simulate time taken to repair
        self.work_hours = self.work_hours - car.repair_time
        self.spent_times.append((car.id, car.spent_time, car.priority))  # Store car ID and spent time
        
        print(f"Mechanic {self.id} finished repairing car {car.id}. It took {car.repair_time} hours.")
        self.total_repairs += 1
    
    async def work(self, queue):
        # Mechanic works until their work hours run out or the queue is empty
        end_time = asyncio.get_event_loop().time() + self.work_hours
        while asyncio.get_event_loop().time() < end_time:
            if queue.empty():
                print(f"Mechanic {self.id} is waiting for cars to repair.")
                
                await asyncio.sleep(0.5)  # Wait before checking again
                continue

            car = await queue.get()  # Unpack the car
            await self.repair(car)  # Repair the dequeued car
            queue.task_done()  # Mark the car as repaired

        print(f"Mechanic {self.id} is done for the day. Total repairs: {self.total_repairs}")

async def main():
    car_queue = PriorityQueue()  # Create a shared queue for cars
    num_cars = 10  # Total number of cars arriving for repair
    spent_times = [] # array to store times of car repairs (used for plotting data)

    # Initialize mechanics with varying efficiency (repair time) and work hours
    mechanic1 = Mechanic(id=1, efficiency=2, work_hours=10)  # Repairs take 2 seconds, works for 20 seconds
    mechanic2 = Mechanic(id=2, efficiency=3, work_hours=10)  # Repairs take 3 seconds, works for 15 seconds

    # Start the enqueue and mechanic processes concurrently
    await asyncio.gather(
        Car.enqueue_cars(car_queue, num_cars),
        mechanic1.work(car_queue),
        mechanic2.work(car_queue)
    )

    await car_queue.join()  # Ensure all cars are processed
    
    spent_times = mechanic1.spent_times + mechanic2.spent_times
    car_ids = [car_id for car_id, _, _ in spent_times]
    times_spent = [time for _, time, _ in spent_times]
    priorities = [priority for _, _, priority in spent_times]
    
    color_map = {0: 'skyblue', 1: 'lightgreen', 2: 'salmon'}
    colors = [color_map[priority] for priority in priorities]

    # Create the bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(car_ids, times_spent, color=colors)
    plt.xlabel('Car ID')
    plt.ylabel('Time Spent in Queue (seconds)')
    plt.title('Time Spent by Each Car in the Queue')
    plt.xticks(car_ids)  # Set x-ticks to be the car IDs
    plt.grid(axis='y')
    # Create legend elements
    legend_elements = [
        Patch(facecolor='skyblue', label='Low Priority (0)'),
        Patch(facecolor='lightgreen', label='Medium Priority (1)'),
        Patch(facecolor='salmon', label='High Priority (2)')
    ]
    plt.legend(handles=legend_elements, title="Car Priority")
    # Show the plot
    plt.show()

# Run the simulation
asyncio.run(main())
