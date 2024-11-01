import asyncio
from asyncio import PriorityQueue
from random import randrange
from time import time

class Car:
    def __init__(self, id, repair_time, priority): 
        self.id = id
        self.repair_time = repair_time 
        self.priority = priority 
        self.arrival_time = None 
        self.repair_start_time = None
        self.spent_time = None
        
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
            await queue.put(car) 
            car.set_arrival_time()
            
            print(f"Car {car.id} with {car.priority} priority added to the queue.")
            
            await asyncio.sleep(0.25) 
        
        
class Mechanic:
    def __init__(self, id, efficiency, work_hours):
        self.id = id
        self.efficiency = efficiency
        self.work_hours = work_hours
        self.total_repairs = 0
        self.spent_times = []  

    async def repair(self, car):
        car.set_queue_duration()
        print(f"Mechanic {self.id} started repairing car {car.id} with {car.priority} priority. It will take {car.repair_time / self.efficiency} hours.")
        
        await asyncio.sleep(car.repair_time / self.efficiency)  
        self.work_hours = self.work_hours - car.repair_time
        self.spent_times.append((car.id, car.spent_time, car.priority))  
        
        print(f"Mechanic {self.id} finished repairing car {car.id}. It took {car.repair_time} hours.")
        self.total_repairs += 1
    
    async def work(self, queue):
        end_time = asyncio.get_event_loop().time() + self.work_hours
        while asyncio.get_event_loop().time() < end_time:
            if queue.empty():
                print(f"Mechanic {self.id} is waiting for cars to repair.")
                
                await asyncio.sleep(0.5)
                continue

            car = await queue.get() 
            await self.repair(car)  
            queue.task_done()  

        print(f"Mechanic {self.id} is done for the day. Total repairs: {self.total_repairs}")