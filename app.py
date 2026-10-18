import streamlit as st
from pawpal_system import *

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_ICON = {Priority.HIGH: "🔴", Priority.MEDIUM: "🟡", Priority.LOW: "🟢"}
SORT_OPTIONS = {"Priority": "priority", "Start time": "time", "Duration": "duration"}


def fmt_time(t):
    return t.strftime("%H:%M") if t else "--:--"


def fmt_priority(p):
    return f"{PRIORITY_ICON[p]} {p.name.lower()}"


def task_rows(tasks, show_status=True):
    """Turn tasks into dict rows for st.table."""
    rows = []
    for t in tasks:
        row = {
            "start": fmt_time(t.start_time),
            "pet": t.pet.name if t.pet else "",
            "task": t.name,
            "type": t.task_type.value,
            "duration": f"{t.duration} min",
            "priority": fmt_priority(t.priority),
            "repeats": t.frequency.value,
            "due": t.due_date.isoformat(),
        }
        if show_status:
            row["status"] = "✅ done" if t.completed else "⏳ pending"
        rows.append(row)
    return rows


st.title("🐾 PawPal+")
st.caption("Plan pet care around your time, priorities and availability.")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="John Doe")

owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

with st.expander("Preferences"):
    st.caption("The schedule respects these limits. Leave them off for no constraints.")
    cap = st.number_input("Max care minutes per day (0 = no limit)", min_value=0, max_value=1440, value=0)
    limit_hours = st.checkbox("Only schedule within my available hours")
    earliest = latest = None
    if limit_hours:
        h1, h2 = st.columns(2)
        earliest = h1.time_input("Earliest", value=time(7, 0))
        latest = h2.time_input("Latest", value=time(21, 0))
        if earliest >= latest:
            st.error("Earliest must be before latest; hours limit ignored.")
            earliest = latest = None
    if cap or earliest:
        owner.preferences = Preferences(
            max_daily_minutes=int(cap) or None, earliest=earliest, latest=latest
        )
    else:
        owner.preferences = None

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
        view = Scheduler(owner=owner, time_available=0)  # budget is irrelevant for viewing

        st.markdown("#### Current tasks")
        conflicts = view.find_conflicts()
        if conflicts:
            st.warning(f"{len(conflicts)} scheduling conflict(s) found:")
            for w in conflicts:
                st.warning(w)
        else:
            st.success("No scheduling conflicts.")

        upcoming = view.next_up()
        if upcoming:
            st.info(
                f"⏭️ Next up: **{upcoming.name}** for {upcoming.pet.name} at "
                f"{fmt_time(upcoming.start_time)} ({upcoming.duration} min)"
            )

        f1, f2, f3, f4, f5 = st.columns(5)
        pet_filter = f1.selectbox(
            "Pet", [None, *pets_by_id], format_func=lambda i: "All" if i is None else pets_by_id[i].name
        )
        status_filter = f2.selectbox("Status", ["All", "Pending", "Done"])
        type_filter = f3.selectbox(
            "Type", [None, *TaskType], format_func=lambda t: "All" if t is None else t.value
        )
        priority_filter = f4.selectbox(
            "Priority", [None, *Priority], format_func=lambda p: "All" if p is None else p.name.lower()
        )
        sort_label = f5.selectbox("Sort by", list(SORT_OPTIONS))

        shown = view.filter_tasks(
            pet=pets_by_id.get(pet_filter),
            completed={"All": None, "Pending": False, "Done": True}[status_filter],
            task_type=type_filter,
            priority=priority_filter,
        )
        shown = view.sort_tasks(shown, SORT_OPTIONS[sort_label])
        if shown:
            st.caption(f"Showing {len(shown)} of {len(all_tasks)} task(s), sorted by {sort_label.lower()}.")
            st.table(task_rows(shown))
        else:
            st.info("No tasks match these filters.")

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
                nxt = task.mark_complete()
                st.toast(
                    f"Completed '{task.name}'."
                    + (f" Next one is due {nxt.due_date}." if nxt else "")
                )
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
    prefs = owner.preferences or Preferences()
    budget = min(int(time_available), prefs.max_daily_minutes or int(time_available))

    if plan.tasks:
        st.success(f"Scheduled {len(plan.tasks)} task(s) for today.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Tasks scheduled", len(plan.tasks))
        m2.metric("Minutes planned", plan.total_duration)
        m3.metric("Minutes left", budget - plan.total_duration)

        conflicts = scheduler.find_conflicts(plan.tasks)
        if conflicts:
            st.warning("Some scheduled tasks overlap. Consider moving one:")
            for w in conflicts:
                st.warning(w)
        else:
            st.success("No overlapping tasks in this schedule.")

        st.table(task_rows(plan.tasks, show_status=False))
    else:
        st.warning("Nothing fits. Add tasks or increase the time available.")

    today = date.today()
    skipped = [
        t for t in scheduler.filter_tasks(completed=False)
        if t.due_date <= today and t not in plan.tasks
    ]
    if skipped:
        with st.expander(f"Not scheduled ({len(skipped)})"):
            rows = task_rows(scheduler.sort_tasks(skipped), show_status=False)
            for row, t in zip(rows, scheduler.sort_tasks(skipped)):
                row["why"] = (
                    "outside available hours" if not prefs.allows(t) else "not enough time left"
                )
            st.table(rows)

    for pet in owner.pets:
        with st.expander(f"Daily plan: {pet.name}"):
            st.text(scheduler.daily_plan(pet))
