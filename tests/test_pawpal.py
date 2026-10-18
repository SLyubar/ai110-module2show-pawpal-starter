from datetime import date, time, timedelta

from pawpal_system import (Frequency, Owner, Pet, Priority, Scheduler, Task,
                           TaskType)


def make_task(frequency: Frequency = Frequency.ONCE) -> Task:
    return Task("Morning walk", "Walk around the park", 30,
                Priority.HIGH, TaskType.WALK, frequency, time(8, 0))


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Goldie", 2, "Golden Retriever")
    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1


def test_completing_daily_task_creates_next_day_task():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.DAILY)
    pet.add_task(task)

    nxt = task.mark_complete()

    assert task.completed is True
    assert nxt is not None and nxt is not task
    assert nxt.due_date == date.today() + timedelta(days=1)
    assert nxt.completed is False
    assert (nxt.name, nxt.start_time, nxt.frequency) == (task.name, task.start_time, task.frequency)
    assert nxt.pet is pet and nxt in pet.tasks and len(pet.tasks) == 2


def test_completing_weekly_task_creates_task_seven_days_out():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.WEEKLY)
    pet.add_task(task)

    nxt = task.mark_complete()

    assert nxt.due_date == date.today() + timedelta(days=7)


def test_completing_one_off_task_creates_nothing():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task()
    pet.add_task(task)

    assert task.mark_complete() is None
    assert len(pet.tasks) == 1


def test_completing_twice_does_not_duplicate():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.DAILY)
    pet.add_task(task)

    task.mark_complete()
    assert task.mark_complete() is None
    assert len(pet.tasks) == 2


def test_future_occurrence_not_in_todays_schedule():
    pet = Pet("Goldie", 2, "Golden Retriever")
    task = make_task(Frequency.DAILY)
    pet.add_task(task)
    scheduler = Scheduler(Owner("Jo", [pet]), time_available=120)

    task.mark_complete()

    assert scheduler.schedule().tasks == []


def make_scheduler():
    goldie = Pet("Goldie", 2, "Golden Retriever")
    buddy = Pet("Buddy", 1, "German Shepherd")
    return Scheduler(Owner("Jo", [goldie, buddy]), time_available=300), goldie, buddy


def timed(name, start, minutes):
    return Task(name, "", minutes, Priority.MEDIUM, TaskType.OTHER, start_time=start)


def test_same_time_tasks_for_same_pet_warn():
    scheduler, goldie, _ = make_scheduler()
    assert scheduler.add_task(goldie, timed("Walk", time(8, 0), 30)) == []

    warnings = scheduler.add_task(goldie, timed("Bath", time(8, 0), 20))

    assert len(warnings) == 1 and "same pet" in warnings[0]
    assert len(goldie.tasks) == 2  # still added; a conflict is only a warning


def test_overlap_across_pets_warns():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Walk", time(8, 0), 30))
    scheduler.add_task(buddy, timed("Meds", time(8, 15), 5))

    warnings = scheduler.find_conflicts()

    assert len(warnings) == 1 and "different pets" in warnings[0]
    assert "Goldie" in warnings[0] and "Buddy" in warnings[0]


def test_back_to_back_tasks_do_not_conflict():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Walk", time(8, 0), 30))
    scheduler.add_task(buddy, timed("Meds", time(8, 30), 5))

    assert scheduler.find_conflicts() == []


def test_conflicts_ignore_completed_untimed_and_other_days():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Walk", time(8, 0), 30))
    done = timed("Done", time(8, 0), 30)
    done.completed = True
    scheduler.add_task(buddy, done)
    scheduler.add_task(buddy, Task("Untimed", "", 30, Priority.LOW, TaskType.OTHER))
    tomorrow = timed("Tomorrow", time(8, 0), 30)
    tomorrow.due_date = date.today() + timedelta(days=1)
    scheduler.add_task(buddy, tomorrow)

    assert scheduler.find_conflicts() == []


def test_long_task_conflicts_with_several_later_tasks():
    scheduler, goldie, buddy = make_scheduler()
    scheduler.add_task(goldie, timed("Hike", time(9, 0), 120))
    scheduler.add_task(buddy, timed("A", time(9, 30), 10))
    scheduler.add_task(buddy, timed("B", time(10, 0), 10))
    scheduler.add_task(buddy, timed("C", time(10, 50), 10))

    assert len(scheduler.find_conflicts()) == 3
