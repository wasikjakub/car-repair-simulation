import asyncio
from asyncio import PriorityQueue
from random import randrange

class Car:
    def __init__(self, id, repair_time, priority): 
        self.id = id
        self.repair_time = repair_time
        self.priority = priority
        
    @staticmethod
    async def enqueue_cars(queue, num_cars):
        for i in range(1, num_cars + 1):
            car = Car(i, randrange(1, 9), randrange(3))
            await queue.put((car.priority, car))  # Enqueue as (priority, car)
            print(f"Car {car.id} with {car.priority} priority added to the queue.")
            await asyncio.sleep(0.5)  # Simulate time between cars arriving
        
        
class Mechanic:
    def __init__(self, id, efficiency, work_hours):
        self.id = id
        self.efficiency = efficiency
        self.work_hours = work_hours
        self.total_repairs = 0

    async def repair(self, car):
        print(f"Mechanic {self.id} started repairing car {car.id} with {car.priority} priority. It will take {car.repair_time / self.efficiency} hours.")
        await asyncio.sleep(car.repair_time / self.efficiency)  # Simulate time taken to repair
        self.work_hours = self.work_hours - car.repair_time
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

            priority, car = await queue.get()  # Unpack the tuple (priority, car)
            await self.repair(car)  # Repair the dequeued car
            queue.task_done()  # Mark the car as repaired

        print(f"Mechanic {self.id} is done for the day. Total repairs: {self.total_repairs}")

async def main():
    car_queue = PriorityQueue()  # Create a shared queue for cars
    num_cars = 5  # Total number of cars arriving for repair

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

# Run the simulation
asyncio.run(main())
