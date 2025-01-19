import asyncio
from asyncio import PriorityQueue, Queue
from random import randrange, choice, random
from time import time
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.dates as mdates
from enum import Enum, auto
from colorama import Fore
from numpy.random import exponential

class ObjectClass(Enum):
    RED = auto()
    ORANGE = auto()
    GREEN = auto()
    PINK = auto()
    
    def __str__(self):
        return self.name


class Car:
    def __init__(self, id): 
        self.id = id
        self.priority = randrange(3) # priority given in FIFO queue (0 priority being the lowest, then order)
        self.arrival_time = None # time when car arrived in queue (enqueued)
        self.repair_start_time = None # time when car started to be repaired
        self.repair_end_time = None # time when mechanic ended repairning
        self.spent_time = None # time spent in queue
        self.end_time = None # time when car left the system
        self.delta_time = None # time spend in system
        self.mechanics_route = [] # stores all mechanics car went through
        self.object_class = choice(list(ObjectClass)) # 90% damage, 60% damage, 30% damage or 0 damage
        self.original_class = self.object_class
        self.destroyed = False
        
        match self.object_class:
            case ObjectClass.RED:
                self.repair_time = [exponential(2) for _ in range(3)]
            case ObjectClass.ORANGE:
                self.repair_time = [exponential(2) for _ in range(2)]
            case ObjectClass.GREEN:
                self.repair_time = [exponential(2) for _ in range(1)]
        
    def set_arrival_time(self):
        self.arrival_time = time() 
        
    def set_end_time(self):
        self.end_time = time()
        self.delta_time = self.end_time - self.arrival_time
        
    def set_queue_duration(self):
        self.repair_start_time = time()
        if self.repair_start_time is not None and self.arrival_time is not None:
            self.spent_time = self.repair_start_time - self.arrival_time
            
    def set_repair_end_time(self):
        self.repair_end_time = time()
        
    def __lt__(self, other):
        return self.priority > other.priority
        
        
class Parking:
    def __init__(self, max_num_cars):
        self.max_num_cars = max_num_cars
        
    async def work(self, queue, **queues):
        last_car_id = 0
        while last_car_id < self.max_num_cars:
            if queue.empty():
                await asyncio.sleep(0.01)  # Wait before checking again
                continue
            
            await asyncio.sleep(exponential(0.1))
            car = await queue.get()  # Unpack the car
            last_car_id = car.id
            match car.object_class:
                case ObjectClass.RED:
                    queue.task_done()
                    if random() < 0.2:
                        car.destroyed = True
                        print(Fore.RED + f"Car {car.id} can not be repaired")
                    else:
                        await enqueue_car(queues['warsztat_queue'], car)
                case ObjectClass.ORANGE:
                    queue.task_done()
                    if random() < 0.5:                   
                        await enqueue_car(queues['warsztat_queue'], car)
                    elif random() < 0.7:
                        await enqueue_car(queues['elektromechanik_queue'], car)
                    elif random() < 0.9:
                        await enqueue_car(queues['wulkanizator_queue'], car)
                    else:
                        await enqueue_car(queues['lakiernik_queue'], car)
                case ObjectClass.GREEN:
                    queue.task_done()
                    if random() < 0.3:
                        await enqueue_car(queues['warsztat_queue'], car)
                    elif random() < 0.55:
                        await enqueue_car(queues['elektromechanik_queue'], car)
                    elif random() < 0.7:
                        await enqueue_car(queues['wulkanizator_queue'], car)
                    elif random() < 0.95:
                        await enqueue_car(queues['lakiernik_queue'], car)
                    else:
                        await enqueue_car(queues['tapicer_queue'], car)
                case ObjectClass.PINK:
                    queue.task_done()
                    print(Fore.MAGENTA + f"Car {car.id} does not need repair")  


class Mechanic:
    def __init__(self, id, efficiency, work_hours, name):
        self.id = id
        self.efficiency = efficiency
        self.work_hours = work_hours
        self.name = name
        self.total_repairs = 0
        self.spent_times = []  # List to store the spent times in queues for cars repaired by this mechanic
        self.car_routes = []   # List to store car routes through network

    async def repair(self, car):
        car.set_queue_duration()
        print(Fore.YELLOW + f"{self.name} started repairing car {car.id} with {car.priority} priority. It will take {car.repair_time[-1] / self.efficiency} hours.")
        
        await asyncio.sleep(car.repair_time[-1] / self.efficiency)  # Simulate time taken to repair
        self.work_hours = self.work_hours - car.repair_time[-1] / self.efficiency
        
        car.set_repair_end_time()
        self.spent_times.append((car.id, car.spent_time, car.priority, car.repair_start_time, car.repair_end_time, car.object_class))
        print(Fore.GREEN + f"{self.name} finished repairing car {car.id}. It took {car.repair_time.pop() / self.efficiency} hours.")
        self.total_repairs += 1
    
    async def work(self, queue, parking_type, **queues):
        # Mechanic works until their work hours run out or the queue is empty
        end_time = asyncio.get_event_loop().time() + self.work_hours
        while asyncio.get_event_loop().time() < end_time:
            if queue.empty():
                # print(f"Mechanic {self.id} is waiting for cars to repair.")
                self.work_hours -= 0.1
                await asyncio.sleep(0.1)  # Wait before checking again
                continue

            car = await queue.get()  # Unpack the car
            if self.work_hours - car.repair_time[-1] / self.efficiency < -1:
                print(Fore.RED + f"{self.name} will not repair car {car.id}. It takes {-(self.work_hours - car.repair_time[-1] / self.efficiency)} hours overtime.")
                continue
            elif self.work_hours - car.repair_time[-1] / self.efficiency < 0:
                print(Fore.YELLOW + f"{self.name} will repair car {car.id}. It takes {-(self.work_hours - car.repair_time[-1] / self.efficiency)} hours overtime.")
            
            await self.repair(car)  # Repair the dequeued car
            await asyncio.sleep(0.1)  # Wait before checking again
            self.work_hours -= 0.1
            
            match parking_type:
                case 'warsztat':
                    match car.object_class:
                        case ObjectClass.RED:
                            queue.task_done()
                            car.object_class = ObjectClass.ORANGE
                            if random() < 0.4:                       
                                await enqueue_car(queues['lakiernik_queue'], car)
                            elif random() < 0.7:
                                await enqueue_car(queues['elektromechanik_queue'], car)
                            else:
                                await enqueue_car(queues['wulkanizator_queue'], car)
                        case ObjectClass.ORANGE:
                            # BRAKUJE NA WYKRESIE - TRZEBA BEDZIE ZMIENIC
                            queue.task_done()
                            car.object_class = ObjectClass.GREEN
                            if random() < 0.5:
                                await enqueue_car(queues['elektromechanik_queue'], car)
                            else:
                                await enqueue_car(queues['wulkanizator_queue'], car)
                        case ObjectClass.GREEN:
                            queue.task_done()
                            car.set_end_time()
                            car.object_class = ObjectClass.PINK
                            print(Fore.MAGENTA + f"Car {car.id} is fully repaired now")
                            self.car_routes.append((car.id, car.mechanics_route))
                case 'lakiernik':
                    match car.object_class:
                        case ObjectClass.ORANGE:
                            queue.task_done()
                            car.object_class = ObjectClass.GREEN
                            await enqueue_car(queues['tapicer_queue'], car)
                        case ObjectClass.GREEN:
                            queue.task_done()
                            car.set_end_time()
                            car.object_class = ObjectClass.PINK
                            print(Fore.MAGENTA + f"Car {car.id} is fully repaired now")
                            self.car_routes.append((car.id, car.mechanics_route))
                case 'elektromechanik':
                    match car.object_class:
                        case ObjectClass.ORANGE:
                            queue.task_done()
                            car.object_class = ObjectClass.GREEN
                            if random() < 0.5:
                                await enqueue_car(queues['wulkanizator_queue'], car)
                            elif random() < 0.9:
                                await enqueue_car(queues['lakiernik_queue'], car)
                            else:
                                await enqueue_car(queues['tapicer_queue'], car)
                        case ObjectClass.GREEN:
                            queue.task_done()
                            car.set_end_time()
                            car.object_class = ObjectClass.PINK
                            print(Fore.MAGENTA + f"Car {car.id} is fully repaired now")
                            self.car_routes.append((car.id, car.mechanics_route))
                case 'wulkanizator':
                    match car.object_class:
                        case ObjectClass.ORANGE:
                            queue.task_done()
                            car.object_class = ObjectClass.GREEN
                            if random() < 0.7:
                                await enqueue_car(queues['lakiernik_queue'], car)
                            else:
                                await enqueue_car(queues['tapicer_queue'], car)
                        case ObjectClass.GREEN:
                            queue.task_done()
                            car.set_end_time()
                            car.object_class = ObjectClass.PINK
                            print(Fore.MAGENTA + f"Car {car.id} is fully repaired now")
                            self.car_routes.append((car.id, car.mechanics_route))
                case 'tapicer':
                    queue.task_done()
                    car.set_end_time()
                    car.object_class = ObjectClass.PINK
                    print(Fore.MAGENTA + f"Car {car.id} is fully repaired now")
                    self.car_routes.append((car.id, car.mechanics_route))
                
                                                    
        print(Fore.WHITE + f"{self.name} is done for the day. Total repairs: {self.total_repairs}")


@staticmethod
async def enqueue_cars(queue, num_cars, all_cars):
    for i in range(1, num_cars + 1):
        car = Car(i)
        all_cars.append(car)
        await queue.put(car)  # Enqueue as (priority, car)
        car.set_arrival_time()
        
        print(Fore.CYAN + f"Car {car.id} with {car.priority} priority of {car.object_class} class arrived at the parking.")
        
        await asyncio.sleep(exponential(1))  # Simulate time between cars arriving
        
@staticmethod
async def enqueue_car(queue, car):
    await queue.put(car)
    car.mechanics_route.append(queue.name)
    print(Fore.CYAN + f"Car {car.id} with {car.priority} priority of {car.object_class} class added to the {queue}")
                
class PriorityQueue(PriorityQueue):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        
    def __str__(self):
        return self.name


async def main():
    ### SIMULATION START ###
    parking_queue = Queue()  # Create a shared queue for cars
    warsztat_queue = PriorityQueue('Warsztat')
    lakiernik_queue = PriorityQueue('Lakiernik')
    elektromechanik_queue = PriorityQueue('Elektromechanik')
    wulkanizator_queue = PriorityQueue('Wulkanizator')
    tapicer_queue = PriorityQueue('Tapicer')
    num_cars = 15  # Total number of cars arriving for repair
    car_data = [] # array to store times of car repairs (used for plotting data) 
    mechanic_data = []
    car_routes = [] # array to store all cars routes
    all_cars = []

    # Initialize mechanics with varying efficiency (repair time) and work hours
    parking = Parking(num_cars)
    warsztat1 = Mechanic(id=1, efficiency=1, work_hours=16, name='Warsztat')
    warsztat2 = Mechanic(id=6, efficiency=1, work_hours=8, name='Warsztat2')
    lakiernik1 = Mechanic(id=2, efficiency=1, work_hours=16, name='Lakiernik')
    elektromechanik1 = Mechanic(id=3, efficiency=1, work_hours=16, name='Elektromechanik')
    wulkanizator1 = Mechanic(id=4, efficiency=1, work_hours=16, name='Wulkanizator')
    tapicer1 = Mechanic(id=5, efficiency=1, work_hours=16, name='Tapicer')
    mechanics = [warsztat1, lakiernik1, elektromechanik1, wulkanizator1, tapicer1, warsztat2]
    
    # Start the enqueue and mechanic processes concurrently
    simulation_start_time = time()
    await asyncio.gather(
        enqueue_cars(parking_queue, num_cars, all_cars),
        parking.work(parking_queue, parking_type='parking', warsztat_queue=warsztat_queue, elektromechanik_queue=elektromechanik_queue, wulkanizator_queue=wulkanizator_queue, lakiernik_queue=lakiernik_queue, tapicer_queue=tapicer_queue),
        warsztat1.work(warsztat_queue, parking_type='warsztat', elektromechanik_queue=elektromechanik_queue, wulkanizator_queue=wulkanizator_queue, lakiernik_queue=lakiernik_queue),
        warsztat2.work(warsztat_queue, parking_type='warsztat', elektromechanik_queue=elektromechanik_queue, wulkanizator_queue=wulkanizator_queue, lakiernik_queue=lakiernik_queue),
        lakiernik1.work(lakiernik_queue, parking_type='lakiernik', tapicer_queue=tapicer_queue),
        elektromechanik1.work(elektromechanik_queue, parking_type='elektromechanik', wulkanizator_queue=wulkanizator_queue, lakiernik_queue=lakiernik_queue, tapicer_queue=tapicer_queue),
        wulkanizator1.work(wulkanizator_queue, parking_type='wulkanizator', lakiernik_queue=lakiernik_queue, tapicer_queue=tapicer_queue),
        tapicer1.work(tapicer_queue, parking_type='tapicer')
    )
    simulation_end_time = time()

    # The line below stops simulation so
    # await car_queue.join()  # Ensure all cars are processed  
    ### SIMULATION END ###
    
    ####################################
    ### PROCESSING DATA FOR PLOTS (CARS) 
    for mechanic in mechanics:
        car_data += mechanic.spent_times  
        car_routes += mechanic.car_routes           
    print(car_routes)
    
    # Extract car details
    car_ids = [car.id for car in all_cars]
    times_spent = []
    for car in all_cars:    
        if car.delta_time and not car.destroyed:
            times_spent.append(car.delta_time)
        elif car.delta_time is None and car.object_class is not ObjectClass.PINK and not car.destroyed:
            times_spent.append(simulation_end_time - car.arrival_time)
        else:
            times_spent.append(0)
    priorities = [car.priority for car in all_cars]
    car_classes = [car.original_class for car in all_cars]
    
    # Map priorities to colors
    color_map = {0: 'skyblue', 1: 'lightgreen', 2: 'salmon'}
    class_map = {ObjectClass.RED: 'red', ObjectClass.ORANGE: 'orange', ObjectClass.GREEN: 'green', ObjectClass.PINK: 'pink'}
    colors = [color_map[priority] for priority in priorities]  # Fixed line
    colors = [class_map[car_class] for car_class in car_classes]

    # Create the bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(car_ids, times_spent, color=colors)
    plt.xlabel('Car ID')
    plt.ylabel('Time spent in system (hours)')
    plt.title('Time spent by each car in the system')
    plt.xticks(car_ids)  # Set x-ticks to be the car IDs
    plt.grid(axis='y')

    # Create legend elements
    legend_elements = [
        Patch(facecolor='red', label='Red class'),
        Patch(facecolor='orange', label='Orange class'),
        Patch(facecolor='green', label='Green class')
    ]
    plt.legend(handles=legend_elements, title="Car original class")

    # Show the plot
    plt.show()


    #########################################
    ### PROCESSING DATA FOR PLOTS (MECHANICS)
    for index, mechanic in enumerate(mechanics):
        mechanic_data += (index + 1, mechanic.spent_times)
    
    mechanics_id = []
    mechanics_times = []
    car_classes = []
    car_ids = []

    for i in range(0, len(mechanic_data), 2):
        mech_id = mechanic_data[i]
        mechanic_entries = mechanic_data[i + 1] 
        
        mechanics_id.append(mech_id)
        times = [(start - simulation_start_time, end - simulation_start_time) for _, _, _, start, end, _ in mechanic_entries]
        mechanics_times.append(times)
        
        cars = [car_class for _, _, _, _, _, car_class in mechanic_entries]
        car_classes.append(cars)
        
        cars = [car_id for car_id, _, _, _, _, _ in mechanic_entries]
        car_ids.append(cars) 
    
    fig, ax = plt.subplots(figsize=(10, 5))
    color_map = {
        ObjectClass.RED: "red",
        ObjectClass.ORANGE: "orange",
        ObjectClass.GREEN: "green",
        ObjectClass.PINK: "pink"
    }    
    for i, (mechanic_times, mechanic_classes, mechanic_car_ids) in enumerate(zip(mechanics_times, car_classes, car_ids)):
        for (start, end), car_class, car_id in zip(mechanic_times, mechanic_classes, mechanic_car_ids):
            # Get the color corresponding to the car_class
            color = color_map[car_class]
            # Plot the line
            ax.plot([start, end], [i, i], color=color, linewidth=10, solid_capstyle="butt")
            # Add the car_id as a small number next to the bar
            mid_point = (start + end) / 2  # Calculate the midpoint of the bar
            ax.text(mid_point, i, str(car_id), color="black", ha="center", va="center", fontsize=8)

            
    # Customize the plot
    ax.set_yticks(range(len(mechanics_times)))
    ax.set_yticklabels([mechanic.name for mechanic in mechanics])
    ax.set_xlabel("Time (hours)")
    ax.set_title("Mechanic schedule")

    plt.grid()
    plt.tight_layout()
    plt.show()

# Run the simulation
asyncio.run(main())
