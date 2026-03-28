import math
import textwrap
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

from db import *
from models import Teacher, Lesson, Schedule, Auditory, LessonType

# ====== Конфигурация ======
TOKEN = "1801875928:AAHuJpGlz5YC3z_Aw1Y784W2Qmxbj89Qcwg"  # Замените на свой

EMOJIES = {
    LessonType.LECTURE: "📚",
    LessonType.PRACTICAL: "✏", #pencil emoji
    LessonType.LAB: "🧪",
}

# ====== Утилиты ======
def chunk_list(lst, chunk_size):
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]

# ====== Главное меню ======
def main_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅️ Пред. неделя", callback_data="prev_week"),
                InlineKeyboardButton("🏠 Главная", callback_data="home"),
                InlineKeyboardButton("➡️ След. неделя", callback_data="next_week"),
            ],
            [
                InlineKeyboardButton(
                    "🔍 Поиск по преподавателям", callback_data="search_teacher"
                ),
                InlineKeyboardButton(
                    "🔍 Поиск по предметам", callback_data="search_subject"
                ),
            ],
        ]
    )

# ====== Клавиатура поиска ======
def gen_search_keyboard(items: list, prefix: str, page: int):
    total = len(items)
    pages = math.ceil(total / 6)
    start = page * 6
    display = items[start : start + 6]

    rows = []
    # Две кнопки в строке
    for chunk in chunk_list(list(enumerate(display, start)), 2):
        icon = "👤" if prefix == "teacher" else "📚"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {item.full_name if prefix=='teacher' else item.name}",
                    callback_data=f"{prefix}_{idx}",
                )
                for idx, item in chunk
            ]
        )

    # Навигация
    prev_page = (page - 1) % pages
    next_page = (page + 1) % pages
    rows.append(
        [
            InlineKeyboardButton("⬅️ Пред. стр.", callback_data=f"{prefix}_prev"),
            InlineKeyboardButton("🏠 Главная", callback_data="home"),
            InlineKeyboardButton("➡️ След. стр.", callback_data=f"{prefix}_next"),
        ]
    )
    return InlineKeyboardMarkup(rows)

# ====== Форматирование расписания ======
def format_schedule(schedules: list[Schedule], week_slot: int) -> str:
    week_slot = int(week_slot)
    # Привязанные даты для каждого week_slot
    date_ranges = {
        0: "28.04 - 03.05",
        1: "21.04 - 26.04",
    }
    # Даты по дням недели для каждого week_slot
    date_labels = {
        0: ["28.04", "29.04", "30.04", "01.05", "02.05", "03.05"],
        1: ["21.04", "22.04", "23.04", "24.04", "25.04", "26.04"],
    }
    # Фильтруем нужную неделю
    week = [s for s in schedules if s.week_slot == week_slot]
    # Сортируем по дню и паре
    week.sort(key=lambda s: (s.day_index, s.period))

    days = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
    ]
    # Заголовок с датами недели
    text = [f"== 🗓 Расписание ({date_ranges[week_slot]}) =="]
    for di in range(6):
        day_entries = [s for s in week if s.day_index == di]
        # Добавляем дату к названию дня
        day_date = date_labels[week_slot][di]
        text.append(f"\n*= 📆 {days[di]} ({day_date}) =*")
        if day_entries:
            for s in day_entries:
                lesson = next((l for l in list_lessons() if l.id == s.lesson_id), None)
                aud = next((a for a in list_auditories() if a.id == s.auditory_id), None)
                teacher_id = lesson.teachers_by_type[s.lesson_type]
                teacher = next((t for t in list_teachers() if t.id == teacher_id), None)
                emoji = EMOJIES[s.lesson_type]

                text.append(
                    f"-- {s.period} пара --\n"
                    f"  {emoji} {lesson.name} ({s.lesson_type.value})\n"
                    f"  Аудитория: {aud.name}\n"
                    f"  Преподаватель: {teacher.full_name}, {teacher.academic_degree}"
                )
        else:
            text.append("  😴 Пар нет")
    return "\n".join(text)

# ====== Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "week_slot" not in context.user_data:
        context.user_data["week_slot"] = 1
    context.user_data["page_teacher"] = 0
    context.user_data["page_subject"] = 0

    schedule_text = format_schedule(list_schedules(), context.user_data["week_slot"])
    escape_chars = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        schedule_text = schedule_text.replace(char, f'\{char}')

    kb = main_menu_keyboard()

    if update.callback_query:
        await update.callback_query.edit_message_text(
            textwrap.dedent(schedule_text),
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN_V2
            )
    else:
        await update.message.reply_text(
            textwrap.dedent(schedule_text),
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN_V2
            )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()

    # Главные кнопки
    if data == "home":
        await start(update, context)
        return
    if data == "prev_week":
        if context.user_data["week_slot"] == "0":
            context.user_data["week_slot"] = "1"
        else:
            context.user_data["week_slot"] = "0"
        await start(update, context)
        return
    if data == "next_week":
        if context.user_data["week_slot"] == "0":
            context.user_data["week_slot"] = "1"
        else:
            context.user_data["week_slot"] = "0"
        await start(update, context)
        return

    # Поиск преподавателя
    if data == "search_teacher":
        teachers = list_teachers()
        page = context.user_data.get("page_teacher", 0)
        kb = gen_search_keyboard(teachers, "teacher", page)
        await update.callback_query.edit_message_text(
            "Выберите преподавателя:", reply_markup=kb
        )
        return
    if data == "teacher_prev" or data == "teacher_next":
        teachers = list_teachers()
        total_pages = math.ceil(len(teachers) / 6)
        page = context.user_data.get("page_teacher", 0)
        page = (page - 1) % total_pages if data.endswith("prev") else (page + 1) % total_pages
        context.user_data["page_teacher"] = page
        kb = gen_search_keyboard(teachers, "teacher", page)
        await update.callback_query.edit_message_text(
            "Выберите преподавателя:", reply_markup=kb
        )
        return
    if data.startswith("teacher_") and data.split("_")[1].isdigit():
        idx = int(data.split("_")[1])
        teacher_obj = list_teachers()[idx]
        # Карточка преподавателя
        text = (
            f"👤 Преподаватель\n"
            f"🆔 ID: {teacher_obj.id}\n"
            f"📛 Имя: {teacher_obj.full_name}\n"
            f"🎓 Степень: {teacher_obj.academic_degree}"
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📚 Предметы", callback_data=f"teacher_subjects_{idx}"),
                InlineKeyboardButton("📅 Расписание", callback_data=f"teacher_schedule_{idx}")
            ],
            [
                InlineKeyboardButton("🏠 Главная", callback_data="home"),
            ],
        ])
        await update.callback_query.edit_message_text(text, reply_markup=kb)
        return
    if data.startswith("teacher_subjects_") and not data.startswith("teacher_schedule_"):
        idx = int(data.split("_")[2])
        teacher_obj = list_teachers()[idx]
        lessons = [
            (i, l) for i, l in enumerate(list_lessons())
            if teacher_obj.id in l.teachers_by_type.values()
        ]
        buttons = []
        for i, (lesson_idx, lesson_obj) in enumerate(lessons):
            if i % 2 == 0:
                buttons.append([])
            buttons[-1].append(
                InlineKeyboardButton(f"📚 {lesson_obj.name}", callback_data=f"subject_{lesson_idx}")
            )
        buttons.append([InlineKeyboardButton("🏠 Главная", callback_data="home")])
        kb = InlineKeyboardMarkup(buttons)
        # Заменяем только клавиатуру, текст карточки остаётся
        await update.callback_query.edit_message_reply_markup(reply_markup=kb)
        return
    if data.startswith("teacher_schedule_") and not any(part in data for part in ("_prev_", "_next_")):
        idx = int(data.split("_")[2])
        teacher_obj = list_teachers()[idx]
        sch = [s for s in list_schedules()
            if (lesson := get_lesson_by_id(s.lesson_id)) and
                lesson.teachers_by_type.get(s.lesson_type) == teacher_obj.id]
        text = f"📅 Расписание {teacher_obj.full_name}:\n" + format_schedule(sch, context.user_data["week_slot"])
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⬅️ Пред. неделя", callback_data=f"teacher_schedule_prev_{idx}"),
                InlineKeyboardButton("🏠 Главная", callback_data="home"),
                InlineKeyboardButton("➡️ След. неделя", callback_data=f"teacher_schedule_next_{idx}"),
            ],
        ])
        await update.callback_query.edit_message_text(text, reply_markup=kb)
        return
    if data.startswith("teacher_schedule_prev_") or data.startswith("teacher_schedule_next_"):
        _, _, direction, idx_str = data.split("_")
        idx = int(idx_str)
        # Переключаем week_slot
        context.user_data["week_slot"] = "0" if context.user_data["week_slot"] == "1" else "1"
        # Повторно рендерим расписание того же преподавателя
        teacher_obj = list_teachers()[idx]
        sch = [s for s in list_schedules()
            if (lesson := get_lesson_by_id(s.lesson_id)) and
                lesson.teachers_by_type.get(s.lesson_type) == teacher_obj.id]
        text = f"📅 Расписание {teacher_obj.full_name}:\n" + format_schedule(sch, context.user_data["week_slot"])
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⬅️ Пред. неделя", callback_data=f"teacher_schedule_prev_{idx}"),
                InlineKeyboardButton("🏠 Главная", callback_data="home"),
                InlineKeyboardButton("➡️ След. неделя", callback_data=f"teacher_schedule_next_{idx}"),
            ],
        ])
        await update.callback_query.edit_message_text(text, reply_markup=kb)
        return


    # Поиск предмета
    if data == "search_subject":
        lessons = list_lessons()
        page = context.user_data.get("page_subject", 0)
        kb = gen_search_keyboard(lessons, "subject", page)
        await update.callback_query.edit_message_text(
            "Выберите предмет:", reply_markup=kb
        )
        return
    if data == "subject_prev" or data == "subject_next":
        lessons = list_lessons()
        total_pages = math.ceil(len(lessons) / 6)
        page = context.user_data.get("page_subject", 0)
        page = (page - 1) % total_pages if data.endswith("prev") else (page + 1) % total_pages
        context.user_data["page_subject"] = page
        kb = gen_search_keyboard(lessons, "subject", page)
        await update.callback_query.edit_message_text(
            "Выберите предмет:", reply_markup=kb
        )
        return
    if data.startswith("subject_") and not data.startswith(("subject_teachers_","subject_schedule_")):
        idx = int(data.split("_")[1])
        lesson_obj = list_lessons()[idx]
        # Составляем строку преподавателей
        teacher_names = []
        for t_id in lesson_obj.teachers_by_type.values():
            t = get_teacher_by_id(t_id)
            teacher_names.append(f"{t.full_name} ({t.id})")
        teachers_str = "\n".join(teacher_names)
        text = (
            f"📚 Предмет\n"
            f"🆔 ID: {lesson_obj.id}\n"
            f"📖 Название: {lesson_obj.name}\n"
            f"👥 Преподаватели:\n{teachers_str}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("👥 Преподаватели", callback_data=f"subject_teachers_{idx}"),
            InlineKeyboardButton("🔍 Расписание", callback_data=f"subject_schedule_{idx}"),
        ],[
            InlineKeyboardButton("🏠 Главная", callback_data="home"),
        ]])
        await update.callback_query.edit_message_text(text, reply_markup=kb)
        return
    if data.startswith("subject_teachers_"):
        idx = int(data.split("_")[2])
        lesson_obj = list_lessons()[idx]
        buttons = []
        for i, t_id in enumerate(lesson_obj.teachers_by_type.values()):
            t = get_teacher_by_id(t_id)
            if i % 2 == 0:
                buttons.append([])
            buttons[-1].append(
                InlineKeyboardButton(f"👤 {t.full_name}", callback_data=f"teacher_{list_teachers().index(t)}")
            )
        buttons.append([InlineKeyboardButton("🏠 Главная", callback_data="home")])
        kb = InlineKeyboardMarkup(buttons)
        # Меняем только клавиатуру, текст карточки не трогаем
        await update.callback_query.edit_message_reply_markup(reply_markup=kb)
        return
    if data.startswith("subject_schedule_") and not any(part in data for part in ("_prev_", "_next_")):
        idx = int(data.split("_")[2])
        lesson_obj = list_lessons()[idx]
        sch = [s for s in list_schedules() if s.lesson_id == lesson_obj.id]
        text = f"📅 Расписание {lesson_obj.name}:\n" + format_schedule(sch, context.user_data["week_slot"])
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⬅️ Пред. неделя", callback_data=f"subject_schedule_prev_{idx}"),
                InlineKeyboardButton("🏠 Главная", callback_data="home"),
                InlineKeyboardButton("➡️ След. неделя", callback_data=f"subject_schedule_next_{idx}"),
            ],
        ])
        await update.callback_query.edit_message_text(text, reply_markup=kb)
        return
    if data.startswith("subject_schedule_prev_") or data.startswith("subject_schedule_next_"):
        _, _, direction, idx_str = data.split("_")
        idx = int(idx_str)
        # Переключаем week_slot
        context.user_data["week_slot"] = "0" if context.user_data["week_slot"] == "1" else "1"
        # Повторно рендерим расписание того же предмета
        lesson_obj = list_lessons()[idx]
        sch = [s for s in list_schedules() if s.lesson_id == lesson_obj.id]
        text = f"📅 Расписание {lesson_obj.name}:\n" + format_schedule(sch, context.user_data["week_slot"])
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⬅️ Пред. неделя", callback_data=f"subject_schedule_prev_{idx}"),
                InlineKeyboardButton("🏠 Главная", callback_data="home"),
                InlineKeyboardButton("➡️ След. неделя", callback_data=f"subject_schedule_next_{idx}"),
            ],
        ])
        await update.callback_query.edit_message_text(text, reply_markup=kb)
        return

# ====== Запуск ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
