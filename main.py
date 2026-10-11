from datetime import time

from pawpal_system import *

# create two pets
goldie = Pet("Goldie", 2, "Golden Retriever")
buddy = Pet("Buddy", 1, "German Shepherd")

# create an owner of the pets
owner = Owner("John Doe", [goldie, buddy])

# create a scheduler for the owner with 3 hours available
scheduler = Scheduler(owner, time_available=180)

# three tasks per pet, each at a different time
scheduler.add_task(goldie, Task("Morning walk", "Walk around the park", 30,
                                Priority.HIGH, TaskType.WALK,
                                Frequency.DAILY, time(8, 0)))
scheduler.add_task(goldie, Task("Breakfast", "One cup of kibble", 10,
                                Priority.HIGH, TaskType.FEED,
                                Frequency.DAILY, time(9, 0)))
scheduler.add_task(goldie, Task("Brushing", "Brush coat", 20,
                                Priority.LOW, TaskType.GROOM,
                                Frequency.WEEKLY, time(17, 30)))

scheduler.add_task(buddy, Task("Morning meds", "Joint supplement", 5,
                               Priority.HIGH, TaskType.MEDS,
                               Frequency.DAILY, time(8, 30)))
scheduler.add_task(buddy, Task("Afternoon walk", "Walk and fetch", 45,
                               Priority.MEDIUM, TaskType.WALK,
                               Frequency.DAILY, time(14, 0)))
scheduler.add_task(buddy, Task("Dinner", "One and a half cups of kibble", 10,
                               Priority.HIGH, TaskType.FEED,
                               Frequency.DAILY, time(18, 0)))

# print each pet's daily plan
for pet in owner.pets:
    print(scheduler.daily_plan(pet))
    print()

# print the combined schedule across all pets
print("Today's schedule (all pets):")
for task in scheduler.schedule().tasks:
    print(f"{task.start_time:%H:%M} - {task.pet.name}: {task.name} "
          f"({task.duration} min) [priority: {task.priority.name.lower()}]")
