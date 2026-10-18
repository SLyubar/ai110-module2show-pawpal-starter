import streamlit as st
from pawpal_system import *

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="John Doe")

owner = st.session_state.owner

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

# ---------------------------------------------------------------- Add a pet
st.subheader("Add a Pet")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    pet_age = st.number_input("Age (years)", min_value=0, max_value=40, value=3)
with col3:
    pet_breed = st.text_input("Breed", value="Shiba Inu")

if st.button("Add pet"):
    try:
        owner.add_pet(Pet(name=pet_name, age=int(pet_age), breed=pet_breed))
        st.success(f"Added {pet_name}.")
    except ValueError as e:
        st.error(str(e))

if owner.pets:
    st.write("Your pets:")
    st.table(
        [{"name": p.name, "age": p.age, "breed": p.breed, "tasks": len(p.tasks)} for p in owner.pets]
    )

    with st.expander("Edit / remove a pet"):
        # selectbox returns copies of objects, so select by id (see below).
        manage_by_id = {p.id: p for p in owner.pets}
        manage_id = st.selectbox(
            "Pet", list(manage_by_id), format_func=lambda i: manage_by_id[i].name, key="manage_pet"
        )
        target = manage_by_id[manage_id]
        k = f"pet_{target.id}"  # per-pet keys so the inputs refill when the selection changes

        col1, col2, col3 = st.columns(3)
        with col1:
            edit_name = st.text_input("Name", value=target.name, key=f"{k}_name")
        with col2:
            edit_age = st.number_input("Age (years)", min_value=0, max_value=40, value=target.age, key=f"{k}_age")
        with col3:
            edit_breed = st.text_input("Breed", value=target.breed, key=f"{k}_breed")

        b1, b2 = st.columns(2)
        if b1.button("Save pet changes"):
            try:
                owner.edit_pet(
                    Pet(name=edit_name, age=int(edit_age), breed=edit_breed, tasks=target.tasks, id=target.id)
                )
                st.toast(f"Updated {edit_name}.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        if b2.button("Remove pet (and its tasks)"):
            try:
                owner.remove_pet(target)
                st.toast(f"Removed {target.name}.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------- Schedule a task
st.subheader("Schedule a Task")

if not owner.pets:
    st.info("Add a pet before scheduling tasks.")
else:
    # st.selectbox returns a *copy* of object options, so select by id and
    # look up the real Pet that lives in owner.pets.
    pets_by_id = {p.id: p for p in owner.pets}
    pet_id = st.selectbox("Pet", list(pets_by_id), format_func=lambda i: pets_by_id[i].name)
    pet_choice = pets_by_id[pet_id]

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox(
            "Priority", list(Priority), index=2, format_func=lambda p: p.name.lower()
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        task_type = st.selectbox("Type", list(TaskType), format_func=lambda t: t.value)
    with col5:
        frequency = st.selectbox("Frequency", list(Frequency), format_func=lambda f: f.value)
    with col6:
        start = st.time_input("Start time", value=time(8, 0))

    if st.button("Add task"):
        # The time budget doesn't matter for adding, so use a placeholder.
        scheduler = Scheduler(owner=owner, time_available=0)
        try:
            warnings = scheduler.add_task(
                pet_choice,
                Task(
                    name=task_title,
                    description="",
                    duration=int(duration),
                    priority=priority,
                    task_type=task_type,
                    frequency=frequency,
                    start_time=start,
                ),
            )
            st.success(f"Added '{task_title}' for {pet_choice.name}.")
            for w in warnings:
                st.warning(w)
        except ValueError as e:
            st.error(str(e))

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("Current tasks:")
        st.table(
            [
                {
                    "pet": t.pet.name if t.pet else "",
                    "task": t.name,
                    "start": t.start_time.strftime("%H:%M") if t.start_time else "--:--",
                    "duration": t.duration,
                    "priority": t.priority.name.lower(),
                    "frequency": t.frequency.value,
                    "done": t.completed,
                }
                for t in all_tasks
            ]
        )
        with st.expander("Edit / remove a task"):
            tasks_by_id = {t.id: t for t in all_tasks}
            task_id = st.selectbox(
                "Task",
                list(tasks_by_id),
                format_func=lambda i: f"{tasks_by_id[i].pet.name}: {tasks_by_id[i].name}",
                key="manage_task",
            )
            task = tasks_by_id[task_id]
            k = f"task_{task.id}"  # per-task keys so the inputs refill when the selection changes

            col1, col2, col3 = st.columns(3)
            with col1:
                new_title = st.text_input("Title", value=task.name, key=f"{k}_name")
            with col2:
                new_duration = st.number_input(
                    "Duration (minutes)", min_value=1, max_value=240, value=task.duration, key=f"{k}_dur"
                )
            with col3:
                new_priority = st.selectbox(
                    "Priority",
                    list(Priority),
                    index=list(Priority).index(task.priority),
                    format_func=lambda p: p.name.lower(),
                    key=f"{k}_pri",
                )
            col4, col5, col6 = st.columns(3)
            with col4:
                new_type = st.selectbox(
                    "Type",
                    list(TaskType),
                    index=list(TaskType).index(task.task_type),
                    format_func=lambda t: t.value,
                    key=f"{k}_type",
                )
            with col5:
                new_freq = st.selectbox(
                    "Frequency",
                    list(Frequency),
                    index=list(Frequency).index(task.frequency),
                    format_func=lambda f: f.value,
                    key=f"{k}_freq",
                )
            with col6:
                new_start = st.time_input("Start time", value=task.start_time or time(8, 0), key=f"{k}_start")

            b1, b2, b3 = st.columns(3)
            if b1.button("Save task changes"):
                # pawpal_system has no edit_task, so update the Task's fields in place.
                task.name = new_title
                task.duration = int(new_duration)
                task.priority = new_priority
                task.task_type = new_type
                task.frequency = new_freq
                task.start_time = new_start
                st.toast(f"Updated '{task.name}'.")
                st.rerun()
            if b2.button("Mark complete", disabled=task.completed):
                task.mark_complete()
                st.toast(f"Completed '{task.name}'.")
                st.rerun()
            if b3.button("Remove task"):
                try:
                    Scheduler(owner=owner, time_available=0).remove_task(task.pet, task)
                    st.toast(f"Removed '{task.name}'.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ----------------------------------------------------------- Build schedule
st.subheader("Build Schedule")
time_available = st.number_input(
    "Time available today (minutes)", min_value=1, max_value=1440, value=60
)

if st.button("Generate schedule"):
    scheduler = Scheduler(owner=owner, time_available=int(time_available))
    plan = scheduler.schedule()
    for w in scheduler.find_conflicts(plan.tasks):
        st.warning(w)
    if plan.tasks:
        st.success(
            f"Scheduled {len(plan.tasks)} task(s), {plan.total_duration} of {int(time_available)} min."
        )
        st.table(
            [
                {
                    "start": t.start_time.strftime("%H:%M") if t.start_time else "--:--",
                    "pet": t.pet.name if t.pet else "",
                    "task": t.name,
                    "duration": t.duration,
                    "priority": t.priority.name.lower(),
                }
                for t in plan.tasks
            ]
        )
    else:
        st.warning("Nothing fits. Add tasks or increase the time available.")

    for pet in owner.pets:
        st.text(scheduler.daily_plan(pet))
