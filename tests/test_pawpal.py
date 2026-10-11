from datetime import time

from pawpal_system import Pet, Priority, Task, TaskType


def make_task() -> Task:
    return Task("Morning walk", "Walk around the park", 30,
                Priority.HIGH, TaskType.WALK, start_time=time(8, 0))


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
