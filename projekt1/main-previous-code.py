import asyncio
from asyncio import PriorityQueue
from random import randrange
from time import time
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.dates as mdates

class Car:
    def __init__(self, id, repair_time, priority): 
        self.id = id
        self.repair_time = repair_time # time needed for mechanic to fix the car (dequeue)
        self.priority = priority # priority given in FIFO queue (0 priority being the lowest, then order)
        self.arrival_time = None # time when car arrived in queue (enqueued)
        self.repair_start_time = None # time when car started to be repaired
        self.repair_end_time = None # time when mechanic ended repairning
        self.spent_time = None # time spent in queue
        
    def set_arrival_time(self):
        self.arrival_time = time() 
        
    def set_queue_duration(self):
        self.repair_start_time = time()
        if self.repair_start_time is not None and self.arrival_time is not None:
            self.spent_time = self.repair_start_time - self.arrival_time
            
    def set_repair_end_time(self):
        self.repair_end_time = time()
        
    def __lt__(self, other):
        return self.priority > other.priority
        
    @staticmethod
    async def enqueue_cars(queue, num_cars):
        for i in range(1, num_cars + 1):
            car = Car(i, randrange(1, 2), randrange(3))
            await queue.put(car)  # Enqueue as (priority, car)
            car.set_arrival_time()
            
            print(f"Car {car.id} with {car.priority} priority added to the queue.")
            
            await asyncio.sleep(0.1)  # Simulate time between cars arriving
        
        
class Mechanic:
    def __init__(self, id, efficiency, work_hours):
        self.id = id
        self.efficiency = efficiency
        self.work_hours = work_hours
        self.total_repairs = 0
        self.spent_times = []  # List to store the spent times in queues for cars repaired by this mechanic

    async def repair(self, car):
        car.set_queue_duration()
        print(f"Mechanic {self.id} started repairing car {car.id} with {car.priority} priority. It will take {car.repair_time / self.efficiency} hours.")
        
        await asyncio.sleep(car.repair_time / self.efficiency)  # Simulate time taken to repair
        self.work_hours = self.work_hours - car.repair_time / self.efficiency
        
        car.set_repair_end_time()
        self.spent_times.append((car.id, car.spent_time, car.priority, car.repair_start_time, car.repair_end_time))
        print(f"Mechanic {self.id} finished repairing car {car.id}. It took {car.repair_time / self.efficiency} hours.")
        self.total_repairs += 1
    
    async def work(self, queue):
        # Mechanic works until their work hours run out or the queue is empty
        end_time = asyncio.get_event_loop().time() + self.work_hours
        while asyncio.get_event_loop().time() < end_time:
            if queue.empty():
                print(f"Mechanic {self.id} is waiting for cars to repair.")
                self.work_hours -= 0.25
                await asyncio.sleep(0.25)  # Wait before checking again
                continue

            car = await queue.get()  # Unpack the car
            if self.work_hours - car.repair_time / self.efficiency < -1:
                print(f"Mechanic {self.id} will not repair car {car.id}. It takes {-(self.work_hours - car.repair_time / self.efficiency)} hours overtime.")
                continue
            elif self.work_hours - car.repair_time / self.efficiency < 0:
                print(f"Mechanic {self.id} will repair car {car.id}. It takes {-(self.work_hours - car.repair_time / self.efficiency)} hours overtime.")
            
            await self.repair(car)  # Repair the dequeued car
            queue.task_done()  # Mark the car as repaired
            await asyncio.sleep(0.1)  # Wait before checking again
            self.work_hours -= 0.1

        print(f"Mechanic {self.id} is done for the day. Total repairs: {self.total_repairs}")

async def main():
    ### SIMULATION START ###
    car_queue = PriorityQueue()  # Create a shared queue for cars
    num_cars = 40  # Total number of cars arriving for repair
    car_data = [] # array to store times of car repairs (used for plotting data) 
    mechanic_data = []

    # Initialize mechanics with varying efficiency (repair time) and work hours
    mechanic1 = Mechanic(id=1, efficiency=2, work_hours=8)
    mechanic2 = Mechanic(id=2, efficiency=2, work_hours=8)
    mechanic3 = Mechanic(id=3, efficiency=2, work_hours=8)
    # mechanic4 = Mechanic(id=4, efficiency=2, work_hours=8)
    mechanics = [mechanic1, mechanic2, mechanic3]
    
    # Start the enqueue and mechanic processes concurrently
    simulation_start_time = time()
    await asyncio.gather(
        Car.enqueue_cars(car_queue, num_cars),
        mechanic1.work(car_queue),
        mechanic2.work(car_queue),
        mechanic3.work(car_queue),
        # mechanic4.work(car_queue)
    )

    # The line below stops simulation so
    # await car_queue.join()  # Ensure all cars are processed  
    ### SIMULATION END ###
    
    ####################################
    ### PROCESSING DATA FOR PLOTS (CARS) 
    for mechanic in mechanics:
        car_data += mechanic.spent_times        
        
    car_ids = [car_id for car_id, _, _, _, _ in car_data]
    times_spent = [time for _, time, _, _, _ in car_data]
    priorities = [priority for _, _, priority, _, _ in car_data]
    
    color_map = {0: 'skyblue', 1: 'lightgreen', 2: 'salmon'}
    colors = [color_map[priority] for priority in priorities]

    # Create the bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(car_ids, times_spent, color=colors)
    plt.xlabel('Car ID')
    plt.ylabel('Time spent in queue (hours)')
    plt.title('Time spent by each car in the queue')
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


    #########################################
    ### PROCESSING DATA FOR PLOTS (MECHANICS)
    for index, mechanic in enumerate(mechanics):
        mechanic_data += (index + 1, mechanic.spent_times)
    
    mechanics_id = []
    mechanics_times = []

    for i in range(0, len(mechanic_data), 2):
        mech_id = mechanic_data[i]
        mechanic_entries = mechanic_data[i + 1]
        
        mechanics_id.append(mech_id)
        times = [(start - simulation_start_time, end - simulation_start_time) for _, _, _, start, end in mechanic_entries]
        mechanics_times.append(times)
        
    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot for each mechanic
    for i, times in enumerate(mechanics_times):
        for start, end in times:
            ax.plot([start, end], [i, i], color="skyblue", linewidth=10, solid_capstyle="butt")
            
    # Customize the plot
    ax.set_yticks(range(len(mechanics_times)))
    ax.set_yticklabels([f"Mechanic {i + 1}" for i in range(len(mechanics_times))])
    ax.set_xlabel("Time (hours)")
    ax.set_title("Mechanic schedule")

    plt.grid()
    plt.tight_layout()
    plt.show()

# Run the simulation
asyncio.run(main())
