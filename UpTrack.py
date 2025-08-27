from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget, TwoLineAvatarIconListItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivy.uix.carousel import Carousel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from datetime import datetime, timedelta
import json
import os
from plyer import notification
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ListProperty
import base64
from kivymd.uix.filemanager import MDFileManager
from kivy.config import Config
from kivy.core.window import Window
from kivmob import KivMob, TestIds
import random
from kivy.utils import get_color_from_hex

# Set flexible window size
Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '700')

class Confetti(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        self.create_confetti()

    def create_confetti(self):
        for _ in range(20):
            x = dp(40) + (self.width - dp(80)) * (0.2 + 0.6 * _ / 20)
            y = dp(40)
            self.particles.append((x, y))

    def animate_confetti(self):
        for i, (x, y) in enumerate(self.particles):
            anim = Animation(y=self.height + dp(40), x=x + dp(-20 + 40 * (i % 2)), duration=1.5, t='in_out_quad')
            anim += Animation(opacity=0, duration=0.5)
            anim.start(self)

class GoalCard(BoxLayout):
    def __init__(self, goals, screen, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(5), **kwargs)
        self.size_hint_y = None
        self.height = dp(300)
        self.screen = screen
        self.goals = goals.copy()
        self.selected_goals = []

        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.95, 0.95, 1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(5))
        
        for i, (goal, is_completed, category, timestamp, reminder_date, streak_day, notes, priority, photo, recurrence) in enumerate(self.goals):
            bullet_text = f"• [b]{'[Completed]' if is_completed else f'[{category}]'}[/b] {goal} ({timestamp}) [P: {priority}]"
            if reminder_date:
                bullet_text += f" [Reminder: {reminder_date}]"
            if streak_day:
                bullet_text += f" [Streak: {streak_day}]"
            if recurrence:
                bullet_text += f" [Recurs: {recurrence}]"
            item_layout = BoxLayout(size_hint_y=None, height=dp(60))
            checkbox = CheckBox(active=False, size_hint=(None, 1), width=dp(30), on_active=lambda x, idx=i: self.toggle_selection(idx))
            item_layout.add_widget(checkbox)
            label = Label(text=bullet_text, markup=True, size_hint_y=None, height=dp(40), color=[0, 0, 0, 1])
            item_layout.add_widget(label)
            toggle_btn = Button(text="✓" if not is_completed else "✗", size_hint=(None, 1), width=dp(40), background_color=[0, 1, 0, 1] if not is_completed else [1, 0, 0, 1], on_press=lambda x, idx=i: self.toggle_complete(idx))
            toggle_btn.bind(on_press=self.animate_button)
            item_layout.add_widget(toggle_btn)
            delete_btn = Button(text="X", size_hint=(None, 1), width=dp(40), background_color=[1, 0, 0, 1], on_press=lambda x, idx=i: self.confirm_delete(idx))
            delete_btn.bind(on_press=self.animate_button)
            item_layout.add_widget(delete_btn)
            note_label = Label(text=f"  - Notes: {notes}", size_hint_y=None, height=dp(20), color=[0, 0, 0, 1])
            layout.add_widget(item_layout)
            layout.add_widget(note_label)
            if photo and is_completed:
                layout.add_widget(Image(source=photo, size_hint=(None, None), size=(dp(100), dp(100))))

        layout.height = len(self.goals) * dp(80)
        scroll.add_widget(layout)
        self.add_widget(scroll)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def animate_button(self, instance):
        original_width = instance.width
        anim = Animation(width=original_width * 1.2, duration=0.1) + Animation(width=original_width, duration=0.1)
        anim.start(instance)

    def toggle_complete(self, index):
        self.screen.toggle_complete(index, self.goals)
        if not self.goals[index][1]:  # Trigger celebration only when marking as complete
            self.screen.celebrate_completion()

    def confirm_delete(self, index):
        self.dialog = MDDialog(
            text=f"Are you sure you want to delete '{self.goals[index][0]}'?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Delete", on_release=lambda x: self.delete_goal(index))
            ]
        )
        self.dialog.open()

    def delete_goal(self, index):
        self.screen.remove_goal(index, refresh_carousel=True)
        self.dialog.dismiss()
        self.clear_widgets()
        self.__init__(self.screen.goals, self.screen)

    def toggle_selection(self, index):
        goal_id = id(self.goals[index])
        if goal_id in self.selected_goals:
            self.selected_goals.remove(goal_id)
        else:
            self.selected_goals.append(goal_id)

class GoalCarousel(Carousel):
    def __init__(self, goals, screen, **kwargs):
        super().__init__(direction='right', **kwargs)
        self.size_hint = (0.6, 1)
        self.pos_hint = {'x': 0.4, 'top': 1}
        self.screen = screen
        self.card = None
        self.update_content(goals)

    def update_content(self, goals):
        self.clear_widgets()
        self.card = GoalCard(goals, self.screen)
        self.add_widget(self.card)
        bulk_action_layout = BoxLayout(size_hint_y=None, height=dp(40))
        bulk_complete_btn = Button(text="Mark Selected Complete", size_hint=(0.5, 1), on_press=self.bulk_complete)
        bulk_delete_btn = Button(text="Delete Selected", size_hint=(0.5, 1), on_press=self.bulk_delete)
        bulk_action_layout.add_widget(bulk_complete_btn)
        bulk_action_layout.add_widget(bulk_delete_btn)
        self.add_widget(bulk_action_layout)

    def bulk_complete(self, instance):
        for i, goal in enumerate(self.screen.goals):
            if id(goal) in self.card.selected_goals:
                self.screen.toggle_complete(i, self.screen.goals)
        self.update_content(self.screen.goals)

    def bulk_delete(self, instance):
        indices_to_delete = [i for i, goal in enumerate(self.screen.goals) if id(goal) in self.card.selected_goals]
        for index in sorted(indices_to_delete, reverse=True):
            self.screen.remove_goal(index, refresh_carousel=False)
        self.update_content(self.goals)

class GoalTrackerScreen(MDScreen):
    view_mode = StringProperty('daily')
    timer_seconds = NumericProperty(1500)  # Default 25 minutes
    break_seconds = NumericProperty(300)
    is_timer_running = False
    is_break = False
    file_manager = None
    goal_carousel = None
    xp = NumericProperty(0)
    level = NumericProperty(1)
    badges = ListProperty([])
    daily_challenge = StringProperty("")
    buddy_progress = StringProperty("Buddy: Not set")
    buddy_goal = StringProperty("")
    pomodoro_sessions = NumericProperty(0)
    custom_focus_time = NumericProperty(25)
    custom_break_time = NumericProperty(5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.goals = []
        self.archived_goals = []
        self.leaderboard = []
        self.load_data()
        self.last_streak_day = None
        self.selected_font = "Roboto"
        self.current_theme = "Blue"
        self.streak_days = 0
        self.total_completed = 0
        self.confetti = None
        self.confetti_sound = SoundLoader.load('confetti.wav')  # Ensure this file exists or handle gracefully
        self.daily_quote = self.get_daily_motivational_quote()
        self.generate_daily_challenge()

        layout = MDBoxLayout(orientation='vertical', padding=dp(5), spacing=dp(5))

        self.title_label = MDLabel(text="Daily Goal Tracker", halign="center", font_style="H5", font_name=self.selected_font)
        layout.add_widget(self.title_label)

        top_bar = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(40))
        self.theme_button = MDRaisedButton(text=f"Set {self.current_theme} Theme", md_bg_color=self.get_palette_color(self.current_theme), on_release=self.cycle_theme)
        top_bar.add_widget(self.theme_button)
        self.mode_button = MDRaisedButton(text="Toggle Light/Dark", md_bg_color=self.get_palette_color(self.current_theme), on_release=self.toggle_mode)
        top_bar.add_widget(self.mode_button)
        self.font_button = MDRaisedButton(text="Font: Roboto", md_bg_color=self.get_palette_color(self.current_theme), on_release=self.toggle_font)
        top_bar.add_widget(self.font_button)
        self.view_toggle = MDRaisedButton(text="Switch to Weekly", md_bg_color=self.get_palette_color(self.current_theme), on_release=self.toggle_view)
        top_bar.add_widget(self.view_toggle)
        self.timer_label = MDLabel(text=f"Focus Timer: {self.custom_focus_time}:00", halign="center", font_name=self.selected_font)
        top_bar.add_widget(self.timer_label)
        self.start_timer_button = MDRaisedButton(text="Start Pomodoro", md_bg_color=self.get_palette_color(self.current_theme), on_release=self.start_pomodoro)
        top_bar.add_widget(self.start_timer_button)
        self.surprise_button = MDRaisedButton(text="Surprise Me Goal", md_bg_color=self.get_palette_color(self.current_theme), on_release=self.generate_surprise_goal)
        top_bar.add_widget(self.surprise_button)
        layout.add_widget(top_bar)

        colors = self.get_theme_colors(MDApp.get_running_app().theme_cls.theme_style == "Dark")
        self.quote_label = MDLabel(text=self.daily_quote, halign="center", text_color=colors["text"], font_name=self.selected_font)
        layout.add_widget(MDBoxLayout(self.quote_label, size_hint_y=None, height=dp(30)))

        self.category_input = MDTextField(
            hint_text="Category (Work/Personal/Health)",
            mode="rectangle",
            size_hint_y=None,
            height=dp(35),
            hint_text_color_normal=colors["hint"],
            hint_text_color_focus=colors["hint"],
            foreground_color=colors["text"]  # Use foreground_color instead of text_color
        )
        layout.add_widget(self.category_input)
        self.priority_input = MDTextField(
            hint_text="Priority (High/Medium/Low)",
            mode="rectangle",
            size_hint_y=None,
            height=dp(35),
            hint_text_color_normal=colors["hint"],
            hint_text_color_focus=colors["hint"],
            foreground_color=colors["text"]
        )
        layout.add_widget(self.priority_input)
        self.goal_input = MDTextField(
            hint_text="Enter your goal",
            mode="rectangle",
            size_hint_y=None,
            height=dp(35),
            hint_text_color_normal=colors["hint"],
            hint_text_color_focus=colors["hint"],
            foreground_color=colors["text"]
        )
        layout.add_widget(self.goal_input)
        self.notes_input = MDTextField(
            hint_text="Add notes/description",
            mode="rectangle",
            size_hint_y=None,
            height=dp(35),
            hint_text_color_normal=colors["hint"],
            hint_text_color_focus=colors["hint"],
            foreground_color=colors["text"]
        )
        layout.add_widget(self.notes_input)
        self.reminder_input = MDTextField(
            hint_text="Reminder Date (YYYY-MM-DD)",
            mode="rectangle",
            size_hint_y=None,
            height=dp(35),
            hint_text_color_normal=colors["hint"],
            hint_text_color_focus=colors["hint"],
            foreground_color=colors["text"]
        )
        layout.add_widget(self.reminder_input)
        self.recurrence_input = MDTextField(
            hint_text="Recurrence (daily/weekly:day/monthly:day)",
            mode="rectangle",
            size_hint_y=None,
            height=dp(35),
            hint_text_color_normal=colors["hint"],
            hint_text_color_focus=colors["hint"],
            foreground_color=colors["text"]
        )
        layout.add_widget(self.recurrence_input)
        self.photo_button = MDRaisedButton(text="Upload Photo", md_bg_color=self.get_palette_color(self.current_theme), on_release=self.upload_photo)
        layout.add_widget(self.photo_button)
        layout.add_widget(MDRaisedButton(text="Add Goal", md_bg_color=self.get_palette_color(self.current_theme), text_color=[1, 1, 0, 1], size_hint_y=None, height=dp(40), on_release=self.add_goal))

        self.progress_bar = MDProgressBar()
        layout.add_widget(self.progress_bar)

        stats_layout = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(30))
        self.counter_label = MDLabel(text="Goals: 0 | Completed: 0 | Streak: 0 days", halign="center", text_color=colors["text"], font_name=self.selected_font)
        stats_layout.add_widget(self.counter_label)
        self.stats_label = MDLabel(text=f"XP: {self.xp} | Level: {self.level} | Badges: {', '.join(self.badges) if self.badges else 'None'} | Pomodoro Sessions: {self.pomodoro_sessions}", halign="center", text_color=colors["text"], font_name=self.selected_font)
        stats_layout.add_widget(self.stats_label)
        layout.add_widget(stats_layout)

        button_layout = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(40))
        button_layout.add_widget(MDRaisedButton(text="View Goals", md_bg_color=self.get_palette_color(self.current_theme), size_hint_x=None, width=dp(90), on_release=self.show_goal_carousel))
        button_layout.add_widget(MDRaisedButton(text="Clear All", md_bg_color=self.get_palette_color(self.current_theme), size_hint_x=None, width=dp(90), on_release=self.clear_all_goals))
        button_layout.add_widget(MDRaisedButton(text="View Leaderboard", md_bg_color=self.get_palette_color(self.current_theme), size_hint_x=None, width=dp(120), on_release=self.show_leaderboard))
        button_layout.add_widget(MDRaisedButton(text="Start Buddy Race", md_bg_color=self.get_palette_color(self.current_theme), size_hint_x=None, width=dp(120), on_release=self.start_buddy_race))
        button_layout.add_widget(MDRaisedButton(text="Set Pomodoro Times", md_bg_color=self.get_palette_color(self.current_theme), size_hint_x=None, width=dp(120), on_release=self.set_pomodoro_times))
        button_layout.add_widget(MDRaisedButton(text="Exit", md_bg_color=[1, 0, 0, 1], size_hint_x=None, width=dp(90), on_release=self.exit_app))
        layout.add_widget(button_layout)

        self.challenge_label = MDLabel(text="Daily Challenge: " + self.daily_challenge, halign="center", text_color=colors["text"], font_name=self.selected_font)
        layout.add_widget(MDBoxLayout(self.challenge_label, size_hint_y=None, height=dp(30)))

        self.add_widget(layout)
        self.update_stats()
        self.update_streak()
        Clock.schedule_interval(self.check_reflection_time, 60)
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True
        )

    def get_theme_colors(self, dark):
        if dark:
            return {
                "hint": get_color_from_hex("#BBBBBB"),  # Light gray for hint text
                "text": get_color_from_hex("#FFFFFF"),  # White for main text
            }
        else:
            return {
                "hint": get_color_from_hex("#666666"),  # Dark gray for hint text
                "text": get_color_from_hex("#000000"),  # Black for main text
            }

    def get_palette_color(self, palette):
        palette_colors = {
            "Blue": [0, 0.5, 1, 1],
            "Green": [0, 0.7, 0, 1],
            "Purple": [0.5, 0, 0.5, 1],
            "Red": [1, 0, 0, 1],
            "Orange": [1, 0.5, 0, 1],
            "Teal": [0, 0.8, 0.8, 1]
        }
        return palette_colors.get(palette, [0, 0.5, 1, 1])

    def cycle_theme(self, instance):
        themes = ["Blue", "Green", "Purple", "Red", "Orange", "Teal"]
        current_index = themes.index(self.current_theme)
        next_index = (current_index + 1) % len(themes)
        self.current_theme = themes[next_index]
        self.theme_button.text = f"Set {self.current_theme} Theme"
        self.set_theme(self.current_theme)
        self.view_toggle.md_bg_color = self.get_palette_color(self.current_theme)
        self.start_timer_button.md_bg_color = self.get_palette_color(self.current_theme)
        self.surprise_button.md_bg_color = self.get_palette_color(self.current_theme)
        self.photo_button.md_bg_color = self.get_palette_color(self.current_theme)

    def set_theme(self, palette):
        MDApp.get_running_app().theme_cls.primary_palette = palette
        self.theme_button.md_bg_color = self.get_palette_color(palette)
        self.mode_button.md_bg_color = self.get_palette_color(palette)
        self.font_button.md_bg_color = self.get_palette_color(palette)
        for child in self.children[0].children:
            if isinstance(child, MDRaisedButton) and child.text != "Exit":
                child.md_bg_color = self.get_palette_color(palette)

    def toggle_mode(self, instance):
        current_mode = MDApp.get_running_app().theme_cls.theme_style
        new_mode = "Dark" if current_mode == "Light" else "Light"
        MDApp.get_running_app().theme_cls.theme_style = new_mode
        self.mode_button.text = f"Toggle {new_mode}/{'Dark' if new_mode == 'Light' else 'Light'}"
        self.update_text_colors()
        Clock.schedule_once(lambda dt: self.rebuild_labels(), 0)

    def rebuild_labels(self):
        for label in [self.title_label, self.quote_label, self.timer_label, self.counter_label, self.stats_label, self.challenge_label]:
            label.texture_update()

    def update_text_colors(self):
        colors = self.get_theme_colors(MDApp.get_running_app().theme_cls.theme_style == "Dark")
        self.category_input.hint_text_color_normal = colors["hint"]
        self.category_input.hint_text_color_focus = colors["hint"]
        self.category_input.foreground_color = colors["text"]
        self.priority_input.hint_text_color_normal = colors["hint"]
        self.priority_input.hint_text_color_focus = colors["hint"]
        self.priority_input.foreground_color = colors["text"]
        self.goal_input.hint_text_color_normal = colors["hint"]
        self.goal_input.hint_text_color_focus = colors["hint"]
        self.goal_input.foreground_color = colors["text"]
        self.notes_input.hint_text_color_normal = colors["hint"]
        self.notes_input.hint_text_color_focus = colors["hint"]
        self.notes_input.foreground_color = colors["text"]
        self.reminder_input.hint_text_color_normal = colors["hint"]
        self.reminder_input.hint_text_color_focus = colors["hint"]
        self.reminder_input.foreground_color = colors["text"]
        self.recurrence_input.hint_text_color_normal = colors["hint"]
        self.recurrence_input.hint_text_color_focus = colors["hint"]
        self.recurrence_input.foreground_color = colors["text"]
        self.title_label.text_color = colors["text"]
        self.quote_label.text_color = colors["text"]
        self.timer_label.text_color = colors["text"]
        self.counter_label.text_color = colors["text"]
        self.stats_label.text_color = colors["text"]
        self.challenge_label.text_color = colors["text"]

    def toggle_font(self, instance):
        current_font = self.selected_font
        fonts = {"Roboto": "Open Sans", "Open Sans": "Lora", "Lora": "Roboto"}
        new_font = fonts.get(current_font, "Roboto")
        try:
            temp_label = MDLabel(text="Test", font_name=new_font)
            temp_label.texture_update()
            self.selected_font = new_font
        except Exception:
            self.selected_font = "Roboto"
            self.show_dialog(f"Font '{new_font}' not found. Please install it (e.g., download from Google Fonts and place as '{new_font}.ttf' in the project directory) or use Roboto.")
        self.font_button.text = f"Font: {self.selected_font}"
        self.title_label.font_name = self.selected_font
        self.counter_label.font_name = self.selected_font
        self.stats_label.font_name = self.selected_font
        self.quote_label.font_name = self.selected_font
        self.timer_label.font_name = self.selected_font
        self.challenge_label.font_name = self.selected_font

    def add_goal(self, instance):
        goal_text = self.goal_input.text.strip()
        category = self.category_input.text.strip() or "General"
        reminder_date = self.reminder_input.text.strip() or None
        notes = self.notes_input.text.strip() or "No notes"
        priority = self.priority_input.text.strip() or "Medium"
        photo = getattr(self, 'selected_photo', None) or None
        recurrence = self.recurrence_input.text.strip() or None
        if goal_text:
            self.goals.append([goal_text, False, category, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reminder_date, None, notes, priority, photo, recurrence])
            self.goal_input.text = ''
            self.category_input.text = ''
            self.notes_input.text = ''
            self.reminder_input.text = ''
            self.priority_input.text = ''
            self.recurrence_input.text = ''
            self.selected_photo = None
            self.save_data()
            self.update_stats()
            self.check_reminders()
            self.update_streak()
            self.auto_archive_goals()
            self.check_challenge_completion(goal_text)
            self.award_xp(10)
        else:
            self.show_dialog("Please enter a goal!")

    def show_goal_carousel(self, instance):
        if not self.goal_carousel:
            goals_to_show = self.goals
            if goals_to_show:
                self.goal_carousel = GoalCarousel(goals_to_show, self)
                self.add_widget(self.goal_carousel)
                anim = Animation(pos_hint={'x': 0, 'top': 1}, duration=0.5)
                anim.start(self.goal_carousel)
                close_button = MDRaisedButton(text="Close", md_bg_color=self.get_palette_color(self.current_theme), size_hint=(0.1, 0.1), pos_hint={'top': 1, 'right': 1}, on_release=self.hide_goal_carousel)
                self.add_widget(close_button)
            else:
                self.show_dialog("No goals to display!")

    def hide_goal_carousel(self, instance):
        if self.goal_carousel:
            anim = Animation(pos_hint={'x': 0.4, 'top': 1}, duration=0.5)
            anim.bind(on_complete=lambda x, y: self.remove_goal_carousel())
            anim.start(self.goal_carousel)

    def remove_goal_carousel(self):
        if self.goal_carousel:
            self.remove_widget(self.goal_carousel)
            self.goal_carousel = None
            for child in self.children[:]:
                if isinstance(child, MDRaisedButton) and child.text == "Close":
                    self.remove_widget(child)

    def toggle_complete(self, index, goals_list):
        global_index = self.goals.index(goals_list[index])
        self.goals[global_index][1] = not self.goals[global_index][1]
        if self.goals[global_index][1]:
            self.goals[global_index][5] = datetime.now().strftime("%Y-%m-%d")
            self.total_completed += 1
            self.celebrate_completion()
            self.award_xp(20)
            self.check_badge_earnings()
            self.check_challenge_completion(self.goals[global_index][0])
        self.save_data()
        self.update_stats()
        self.update_streak()
        self.update_leaderboard()

    def celebrate_completion(self):
        if not self.confetti:
            self.confetti = Confetti()
            self.add_widget(self.confetti)
        self.confetti.animate_confetti()
        if self.confetti_sound:
            self.confetti_sound.play()
        Clock.schedule_once(lambda dt: self.remove_confetti(), 2.0)

    def remove_confetti(self):
        if self.confetti:
            self.remove_widget(self.confetti)
            self.confetti = None

    def remove_goal(self, index, refresh_carousel=False):
        if self.goals[index][1]:
            self.total_completed -= 1
        self.goals.pop(index)
        self.save_data()
        self.update_stats()
        if refresh_carousel and self.goal_carousel:
            self.goal_carousel.update_content(self.goals)
        self.update_leaderboard()

    def clear_all_goals(self, instance):
        self.dialog = MDDialog(
            text="Are you sure you want to clear all goals?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Clear", on_release=lambda x: self.confirm_clear())
            ]
        )
        self.dialog.open()

    def confirm_clear(self):
        self.goals = []
        self.total_completed = 0
        self.streak_days = 0
        self.save_data()
        self.update_stats()
        self.dialog.dismiss()
        self.update_leaderboard()

    def update_stats(self):
        total = len(self.goals)
        completed = sum(1 for goal in self.goals if goal[1])
        self.counter_label.text = f"Goals: {total} | Completed: {completed} | Streak: {self.streak_days} days"
        self.stats_label.text = f"XP: {self.xp} | Level: {self.level} | Badges: {', '.join(self.badges) if self.badges else 'None'} | Pomodoro Sessions: {self.pomodoro_sessions}"

    def save_data(self):
        data = {
            "goals": self.goals,
            "archived_goals": self.archived_goals,
            "leaderboard": self.leaderboard,
            "xp": self.xp,
            "level": self.level,
            "badges": self.badges,
            "daily_challenge": self.daily_challenge,
            "buddy_progress": self.buddy_progress,
            "buddy_goal": self.buddy_goal,
            "pomodoro_sessions": self.pomodoro_sessions,
            "custom_focus_time": self.custom_focus_time,
            "custom_break_time": self.custom_break_time
        }
        with open("gamified_data.json", "w") as f:
            json.dump(data, f)

    def load_data(self):
     if os.path.exists("gamified_data.json"):
        try:
            with open("gamified_data.json", "r") as f:
                data = json.load(f)
                self.goals = data.get("goals", [])
                self.archived_goals = data.get("archived_goals", [])
                self.leaderboard = data.get("leaderboard", [])
                self.xp = data.get("xp", 0)
                self.level = data.get("level", 1)
                self.badges = data.get("badges", [])
                self.daily_challenge = data.get("daily_challenge", "")
                self.buddy_progress = data.get("buddy_progress", "Buddy: Not set")
                self.buddy_goal = data.get("buddy_goal", "")
                self.pomodoro_sessions = data.get("pomodoro_sessions", 0)
                self.custom_focus_time = data.get("custom_focus_time", 25)
                self.custom_break_time = data.get("custom_break_time", 5)

                # Validate and normalize goals
                valid_goals = []
                for goal in self.goals:
                    if not isinstance(goal, list) or len(goal) < 10:
                        # Create a default goal structure if invalid
                        valid_goals.append(["Invalid Goal", False, "General", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None, None, "No notes", "Medium", None, None])
                    else:
                        valid_goals.append(goal)
                self.goals = valid_goals

                # Recalculate total_completed safely
                self.total_completed = sum(1 for goal in self.goals if isinstance(goal, list) and len(goal) > 1 and goal[1])
        except json.JSONDecodeError:
            self.goals = []
            self.archived_goals = []
            self.leaderboard = []
            self.xp = 0
            self.level = 1
            self.badges = []
            self.daily_challenge = ""
            self.buddy_progress = "Buddy: Not set"
            self.buddy_goal = ""
            self.pomodoro_sessions = 0
            self.custom_focus_time = 25
            self.custom_break_time = 5
            self.total_completed = 0

    def exit_app(self, instance):
        self.dialog = MDDialog(
            text="Are you sure you want to exit?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Exit", on_release=lambda x: self.confirm_exit())
            ]
        )
        self.dialog.open()

    def confirm_exit(self):
        if self.ads.is_interstitial_loaded():
            self.ads.show_interstitial()
        self.dialog.dismiss()
        MDApp.get_running_app().stop()

    def show_dialog(self, message):
        self.dialog = MDDialog(
            text=message,
            buttons=[
                MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def check_reminders(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        for goal_data in self.goals:
            if goal_data[4] and goal_data[4] <= current_date and not goal_data[1]:
                notification.notify(
                    title="Goal Reminder",
                    message=f"{goal_data[0]} is due today!",
                    app_name="Goal Tracker"
                )
                self.show_dialog(f"Reminder: {goal_data[0]} is due today!")

    def update_streak(self):
        current_day = datetime.now().strftime("%Y-%m-%d")
        completed_today = any(goal[1] and (goal[5] == current_day if goal[5] else False) for goal in self.goals)
        if completed_today:
            if self.last_streak_day != current_day:
                self.last_streak_day = current_day
                self.streak_days += 1
                for goal in self.goals:
                    if goal[1] and not goal[9]:
                        goal[5] = current_day
                self.save_data()
                self.show_dialog(f"Streak updated! Current streak: {self.streak_days} days")
        elif self.last_streak_day and self.last_streak_day != current_day:
            self.streak_days = 0
            self.last_streak_day = None
            self.save_data()
        self.update_stats()

    def get_daily_motivational_quote(self):
        quotes = [
            "Every day is a new beginning. - T.S. Eliot",
            "The journey of a thousand miles begins with one step. - Lao Tzu",
            "Keep your face always toward the sunshine—and shadows will fall behind you. - Walt Whitman",
            "What you get by achieving your goals is not as important as what you become by achieving your goals. - Zig Ziglar",
            "The future depends on what you do today. - Mahatma Gandhi",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
            "Believe you can and you're halfway there. - Theodore Roosevelt",
            "The best way to predict the future is to create it. - Peter Drucker",
            "You are never too old to set another goal or to dream a new dream. - C.S. Lewis",
            "Hardships often prepare ordinary people for an extraordinary destiny. - C.S. Lewis",
            "The only way to do great work is to love what you do. - Steve Jobs",
            "It does not matter how slowly you go as long as you do not stop. - Confucius",
            "Don’t watch the clock; do what it does. Keep going. - Sam Levenson",
            "The secret of getting ahead is getting started. - Mark Twain",
            "You miss 100% of the shots you don’t take. - Wayne Gretzky"
        ]
        current_date = datetime.now().date()
        index = (current_date.day + current_date.month) % len(quotes)
        return quotes[index]

    def auto_archive_goals(self):
        current_date = datetime.now()
        archive_threshold = current_date - timedelta(days=7)
        self.goals = [goal for goal in self.goals if goal[3] and datetime.strptime(goal[3], "%Y-%m-%d %H:%M:%S") > archive_threshold]
        self.archived_goals = [goal for goal in self.goals if goal[3] and datetime.strptime(goal[3], "%Y-%m-%d %H:%M:%S") <= archive_threshold] + self.archived_goals
        self.save_data()
        self.update_stats()

    def toggle_view(self, instance):
        self.view_mode = 'weekly' if self.view_mode == 'daily' else 'daily'
        self.view_toggle.text = f"Switch to {'Weekly' if self.view_mode == 'daily' else 'Daily'}"

    def start_pomodoro(self, instance):
        if not self.is_timer_running:
            self.is_timer_running = True
            self.is_break = False
            self.timer_seconds = self.custom_focus_time * 60
            self.start_timer_button.text = "Stop Pomodoro"
            Clock.schedule_interval(self.update_timer, 1)
        else:
            self.is_timer_running = False
            self.start_timer_button.text = "Start Pomodoro"
            Clock.unschedule(self.update_timer)

    def update_timer(self, dt):
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            minutes = self.timer_seconds // 60
            seconds = self.timer_seconds % 60
            self.timer_label.text = f"{'Focus' if not self.is_break else 'Break'} Timer: {minutes:02d}:{seconds:02d}"
            if self.timer_seconds <= 60:  # Notification for last minute
                if not hasattr(self, 'timer_alert_played') or not self.timer_alert_played:
                    notification.notify(title="Timer Alert", message=f"{minutes}:{seconds} remaining!", app_name="Goal Tracker")
                    self.timer_alert_played = True
            else:
                self.timer_alert_played = False
        else:
            if not self.is_break:
                self.is_break = True
                self.timer_seconds = self.custom_break_time * 60
                self.pomodoro_sessions += 1
                self.save_data()
                self.update_stats()
                notification.notify(title="Break Time", message=f"Take a {self.custom_break_time}-minute break!", app_name="Goal Tracker")
                self.show_dialog(f"Break time! Take {self.custom_break_time} minutes to rest.")
            else:
                self.is_break = False
                self.timer_seconds = self.custom_focus_time * 60
                notification.notify(title="Focus Time", message=f"Time to focus for {self.custom_focus_time} minutes!", app_name="Goal Tracker")
                self.show_dialog(f"Time to focus! {self.custom_focus_time} minutes start now.")
            self.timer_label.text = f"Focus Timer: {self.custom_focus_time}:00" if not self.is_break else f"Break Timer: {self.custom_break_time}:00"

    def check_reflection_time(self, dt):
        current_time = datetime.now().strftime("%H:%M")
        if current_time == "21:00":
            prompts = ["What was the highlight of your day?", "What could you improve tomorrow?", "What made you proud today?", "How did you stay motivated?", "What did you learn today?"]
            prompt = random.choice(prompts)
            self.show_dialog(f"Daily Reflection: {prompt}")

    def generate_surprise_goal(self, instance):
        presets = [
            ("Complete a 10-minute workout", "Health", "High", "Stay active and energized!"),
            ("Read 5 pages of a book", "Personal", "Medium", "Expand your mind today!"),
            ("Organize your workspace", "Work", "Low", "A tidy space boosts productivity!"),
            ("Meditate for 5 minutes", "Health", "Medium", "Find your inner peace!"),
            ("Write a thank-you note", "Personal", "Low", "Spread positivity today!"),
            ("Learn 5 new words", "Personal", "Medium", "Boost your vocabulary!"),
            ("Cook a healthy meal", "Health", "High", "Nourish your body!"),
            ("Plan your next day", "Work", "Low", "Stay organized!"),
            ("Take a 15-minute walk", "Health", "Medium", "Enjoy some fresh air!"),
            ("Practice a hobby for 20 minutes", "Personal", "Medium", "Unwind and create!"),
            ("Call a friend", "Personal", "Low", "Strengthen your connections!"),
            ("Write a journal entry", "Personal", "Low", "Reflect on your day!"),
            ("Do a 5-minute stretch", "Health", "Medium", "Relieve tension!"),
            ("Watch an educational video", "Work", "Medium", "Learn something new!")
        ]
        goal_text, category, priority, notes = random.choice(presets)
        self.goal_input.text = goal_text
        self.category_input.text = category
        self.priority_input.text = priority
        self.notes_input.text = notes
        self.show_dialog(f"Surprise Goal Generated: {goal_text} [P: {priority}]")

    def upload_photo(self, instance):
        self.file_manager.show('C:/Users/PC/Desktop')

    def select_path(self, path):
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        self.selected_photo = f"data:image/jpeg;base64,{encoded_string}"
        self.file_manager.close()
        self.show_dialog("Photo uploaded successfully!")

    def exit_manager(self, *args):
        self.file_manager.close()

    def generate_daily_challenge(self):
        challenges = [
            ("Run 1 km", 30),
            ("Meditate for 10 minutes", 25),
            ("Read 10 pages", 20),
            ("Drink 2 liters of water", 15),
            ("Complete 20 push-ups", 35),
            ("Learn a new skill", 40)
        ]
        challenge, xp = random.choice(challenges)
        self.daily_challenge = f"{challenge} (+{xp} XP)"
        self.save_data()

    def check_challenge_completion(self, goal_text):
        if goal_text.lower() in self.daily_challenge.lower():
            self.award_xp(30)
            self.badges.append("Challenge Master")
            self.show_dialog(f"Challenge completed! +30 XP and 'Challenge Master' badge earned!")
            self.generate_daily_challenge()

    def award_xp(self, amount):
        self.xp += amount
        while self.xp >= self.level * 100:
            self.level += 1
            self.badges.append(f"Level {self.level}")
            self.show_dialog(f"Level up to {self.level}! Unlocked new badge!")
        self.save_data()
        self.update_stats()

    def check_badge_earnings(self):
        current_time = datetime.now().hour
        if self.total_completed >= 10 and "10 Goals Completed" not in self.badges:
            self.badges.append("10 Goals Completed")
        if self.streak_days >= 7 and "7-Day Streak" not in self.badges:
            self.badges.append("7-Day Streak")
        if current_time < 7 and "Early Bird" not in self.badges:
            self.badges.append("Early Bird")
        self.save_data()
        self.update_stats()

    def update_leaderboard(self):
        username = "User"
        self.leaderboard = sorted(self.leaderboard, key=lambda x: (x[3], x[1], x[2]), reverse=True)
        if not any(u[0] == username for u in self.leaderboard):
            self.leaderboard.append([username, self.total_completed, self.streak_days, self.xp])
        else:
            for entry in self.leaderboard:
                if entry[0] == username:
                    entry[1] = self.total_completed
                    entry[2] = self.streak_days
                    entry[3] = self.xp
                    break
        self.leaderboard = self.leaderboard[:5]
        self.save_data()

    def show_leaderboard(self, instance):
        leaderboard_text = "Leaderboard:\n" + "\n".join([f"{i+1}. {entry[0]} - Completed: {entry[1]}, Streak: {entry[2]}, XP: {entry[3]}" for i, entry in enumerate(self.leaderboard)])
        self.show_dialog(leaderboard_text)

    def start_buddy_race(self, instance):
        if not self.buddy_goal:
            self.buddy_goal = "Complete a 5-minute workout"
            self.buddy_progress = "Buddy: 0%"
            self.show_dialog(f"Buddy Race started! Goal: {self.buddy_goal}. Track progress manually.")
        else:
            progress = int(self.buddy_progress.split(": ")[1].replace("%", ""))
            if progress < 100:
                progress += 25
                self.buddy_progress = f"Buddy: {min(progress, 100)}%"
                self.show_dialog(f"Buddy progress updated to {progress}%!")
                if progress == 100:
                    self.badges.append("Buddy Race Winner")
                    self.show_dialog("You won the Buddy Race! 'Buddy Race Winner' badge earned!")
            self.save_data()

    def set_pomodoro_times(self, instance):
        from kivymd.uix.card import MDCard
        self.dialog = MDDialog(
            title="Set Pomodoro Times",
            type="custom",
            content_cls=MDCard(
                size_hint=(None, None),
                size=(dp(300), dp(200)),
                elevation=10,
                padding=dp(15),
                spacing=dp(10),
                orientation='vertical',
                md_bg_color=[0.9, 0.9, 0.9, 1]  # Light gray background to remove black impression
            ),
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Save", on_release=self.save_pomodoro_times)
            ]
        )
        content = self.dialog.content_cls
        focus_input = MDTextField(
            hint_text="Focus Time (minutes)",
            mode="rectangle",
            text=str(self.custom_focus_time),
            size_hint_x=0.9,
            height=dp(50),
            max_text_length=3,
            padding=dp(10)
        )
        break_input = MDTextField(
            hint_text="Break Time (minutes)",
            mode="rectangle",
            text=str(self.custom_break_time),
            size_hint_x=0.9,
            height=dp(50),
            max_text_length=3,
            padding=dp(10)
        )
        content.add_widget(focus_input)
        content.add_widget(break_input)
        self.dialog.open()

    def save_pomodoro_times(self, instance):
        try:
            self.custom_focus_time = int(self.dialog.content_cls.children[1].text) or 25
            self.custom_break_time = int(self.dialog.content_cls.children[0].text) or 5
            self.timer_label.text = f"Focus Timer: {self.custom_focus_time}:00"
            self.save_data()
            self.dialog.dismiss()
        except ValueError:
            self.show_dialog("Please enter valid numbers for focus and break times!")

class GoalTrackerApp(MDApp):
    def build(self):
        self.ads = KivMob("ca-app-pub-3940256099942544~3347511713")
        self.ads.new_banner(TestIds.BANNER, top_pos=False)
        self.ads.request_banner()
        self.ads.show_banner()
        self.ads.new_interstitial(TestIds.INTERSTITIAL)
        self.ads.request_interstitial()
        return GoalTrackerScreen()

if __name__ == '__main__':
    GoalTrackerApp().run()