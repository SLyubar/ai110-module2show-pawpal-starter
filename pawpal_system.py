from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Pet:
    name: str
    age: int
    breed: str

    def walk(self) -> None:
        pass

    def eat(self) -> None:
        pass

    def sleep(self) -> None:
        pass


@dataclass
class Task:
    name: str
    duration: int
    priority: str
    task_type: str

    def schedule(self) -> None:
        pass

    def complete(self) -> None:
        pass

    def walk(self) -> None:
        pass

    def feed(self) -> None:
        pass

    def give_meds(self) -> None:
        pass

    def groom(self) -> None:
        pass


@dataclass
class Preferences:
    """Placeholder for owner preferences (e.g. preferred times, limits)."""


@dataclass
class Schedule:
    """Placeholder for a schedule of tasks."""
    tasks: List[Task] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)
    schedule: Optional[Schedule] = None
    preferences: Optional[Preferences] = None

    def add_pet(self, pet: Pet) -> None:
        pass

    def edit_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def get_number_of_pets(self) -> int:
        pass


@dataclass
class Scheduler:
    owner_preferences: Preferences
    time_available: int
    duration: int
    priority: str
    tasks: List[Task] = field(default_factory=list)

    def schedule(self) -> Schedule:
        pass

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass
