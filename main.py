from datetime import date, time

from pawpal_system import *

# create two pets
goldie = Pet("Goldie", 2, "Golden Retriever")
buddy = Pet("Buddy", 1, "German Shepherd")

# create an owner of the pets
owner = Owner("John Doe", [goldie, buddy])

# create a scheduler for the owner with 3 hours available
scheduler = Scheduler(owner, time_available=180)

# six tasks added deliberately out of time/priority order
scheduler.add_task(buddy, Task("Dinner", "One and a half cups of kibble", 10,
                               Priority.HIGH, TaskType.FEED,
                               Frequency.DAILY, time(18, 0)))
scheduler.add_task(goldie, Task("Brushing", "Brush coat", 20,
                                Priority.LOW, TaskType.GROOM,
                                Frequency.WEEKLY, time(17, 30)))
scheduler.add_task(goldie, Task("Breakfast", "One cup of kibble", 10,
                                Priority.HIGH, TaskType.FEED,
                                Frequency.DAILY, time(9, 0)))
scheduler.add_task(buddy, Task("Afternoon walk", "Walk and fetch", 45,
                               Priority.MEDIUM, TaskType.WALK,
                               Frequency.DAILY, time(14, 0)))
scheduler.add_task(goldie, Task("Morning walk", "Walk around the park", 30,
                                Priority.HIGH, TaskType.WALK,
                                Frequency.DAILY, time(8, 0)))
scheduler.add_task(buddy, Task("Morning meds", "Joint supplement", 5,
                               Priority.HIGH, TaskType.MEDS,
                               Frequency.DAILY, time(8, 30)))

# mark one task done so the completed filter has something to show
next(t for t in buddy.tasks if t.name == "Morning meds").mark_complete()


def show(title, tasks):
    print(title)
    for t in tasks:
        when = t.start_time.strftime("%H:%M") if t.start_time else "--:--"
        print(f"  {when} {t.pet.name:<6} {t.name:<15} {t.duration:>3} min "
              f"{t.priority.name.lower():<6} {t.task_type.value:<5} "
              f"{'done' if t.completed else 'todo'}")
    print()


show("As added (unsorted):", scheduler.get_tasks())

for key in ("time", "priority", "duration"):
    show(f"Sorted by {key}:", scheduler.sort_tasks(scheduler.get_tasks(), key))

show("Filter: Goldie's tasks", scheduler.filter_tasks(pet=goldie))
show("Filter: completed", scheduler.filter_tasks(completed=True))
show("Filter: Buddy, not completed",
     scheduler.filter_tasks(pet=buddy, completed=False))
show("Filter: walks", scheduler.filter_tasks(task_type=TaskType.WALK))
show("Filter: high priority, not completed, sorted by time",
     scheduler.sort_tasks(
         scheduler.filter_tasks(completed=False, priority=Priority.HIGH), "time"))

nxt = scheduler.next_up(time(10, 0))
print(f"Next up after 10:00: {nxt.start_time:%H:%M} {nxt.pet.name}: {nxt.name}\n")

# print each pet's daily plan
for pet in owner.pets:
    print(scheduler.daily_plan(pet))
    print()

# print the combined schedule across all pets
print("Today's schedule (all pets):")
for task in scheduler.schedule().tasks:
    print(f"{task.start_time:%H:%M} - {task.pet.name}: {task.name} "
          f"({task.duration} min) [priority: {task.priority.name.lower()}]")

# recurring tasks: completing a daily/weekly task creates the next occurrence
print("Recurring tasks:")
for name in ("Morning walk", "Brushing", "Dinner"):
    done = next(t for t in owner.get_all_tasks() if t.name == name and not t.completed)
    nxt = done.mark_complete()
    print(f"  completed {done.pet.name}: {done.name} ({done.frequency.value}) "
          f"-> next due {nxt.due_date} ({(nxt.due_date - date.today()).days} day(s) from today)")
print()
show("Goldie's tasks after completing (new copies are due later):",
     scheduler.filter_tasks(pet=goldie))
print("Still in today's schedule:",
      [t.name for t in scheduler.schedule().tasks])

# conflict detection: warnings are returned, nothing crashes
print("\nConflict detection:")
print("  existing tasks:", scheduler.find_conflicts() or "no conflicts")
for w in scheduler.add_task(goldie, Task("Vet call", "", 30, Priority.MEDIUM,
                                         TaskType.OTHER, start_time=time(14, 15))):
    print(" ", w)
for w in scheduler.add_task(goldie, Task("Bath", "", 20, Priority.LOW,
                                         TaskType.GROOM, start_time=time(14, 30))):
    print(" ", w)
