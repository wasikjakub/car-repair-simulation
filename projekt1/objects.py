import asyncio
from asyncio import PriorityQueue
from random import randrange
from time import time

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